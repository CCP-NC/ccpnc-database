import os
import json
from datetime import timedelta
from flask import Flask, Response, session, request, make_response

from ccpncdb.config import Config
from ccpncdb.magresdb import MagresDB, MagresDBError
from ccpncdb.log import Logger
from ccpncdb.orcid import OrcidConnection, NoOrcidTokens, OrcidError
from ccpncdb.utils import split_data
from ccpncdb.schemas import (magresRecordSchemaUser,
                             magresVersionSchemaUser)
from ccpncdb.archive import MagresArchive, MagresArchiveError


class MainServer(object):

    # Response codes
    HTTP_200_OK = 200
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_500_INTERNAL_SERVER_ERROR = 500

    # Log types
    LOG_ADDRECORD = 0
    LOG_ADDARCHIVE = 1
    LOG_ADDVERSION = 2

    def __init__(self, path=''):

        self._path = path
        self._static_folder = os.path.join(path, 'static')
        self._config_folder = os.path.join(path, 'config')

        self._app = Flask('ccpnc-database', static_url_path='',
                          static_folder=self._static_folder)
        # Load secret key
        with open(os.path.join(path, 'secret', 'secret.key')) as secret:
            self._app.secret_key = secret.read().strip()

        # Set up cookie, duration: one month
        self._app.config['SESSION_COOKIE_NAME'] = 'CCPNCDBLOGIN'
        self._app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

        with open(os.path.join(path, 'secret',
                               'orcid_details.json')) as f:
            self._orcid_details = json.load(f)

        if not hasattr(self._app, 'extensions'):
            self._app.extensions = {}
        self._app.extensions['orcidlink'] = OrcidConnection(
            self._orcid_details, session)
        self._orcid = self._app.extensions['orcidlink']

        self._config = Config(os.path.join(self._config_folder,
                                           'config.json'))
        self._client = self._config.client()
        self._dbname = self._config.db_name
        self._db = MagresDB(client=self._client, dbname=self._dbname)
        self._logger = Logger(client=self._client)

    @property
    def app(self):
        return self._app

    @property
    def orcid(self):
        return self._orcid

    @orcid.setter
    def orcid(self, val):
        self._orcid = val
        self._app.extensions['orcidlink'] = val

    def send_static(self, url):
        return self._app.send_static_file(url)

    def request_user_info(self, auth_admin=False):

        client_details = {
            'orcid': request.values.get('_auth_id', None),
            'access_token': request.values.get('_auth_tk', None)
        }

        try:
            rinfo = self._orcid.request_info(client_details,
                                             auth_admin=auth_admin)
        except OrcidError as e:
            return {'error': str(e)}

        return rinfo

    def logout(self):
        self._orcid.delete_tokens()
        return 'Logged out', self.HTTP_200_OK

    def get_tokens(self, code=None):
        try:
            tk = self._orcid.get_tokens(code)
        except NoOrcidTokens as e:
            return str(e), self.HTTP_401_UNAUTHORIZED

        return json.dumps(tk), self.HTTP_200_OK

    def upload_record(self):

        # First, authenticate
        user_info = self.request_user_info()
        if 'error' in user_info:
            return user_info['error'], self.HTTP_401_UNAUTHORIZED

        # Upload: single, or multiple?
        is_multi = request.values.get('_upload_multi', 'false') == 'true'

        # Fetch the actual magres file
        fd = request.files['magres-file']

        # Now extract the record information
        rdata, vdata = split_data(dict(request.values),
                                  magresRecordSchemaUser,
                                  magresVersionSchemaUser)
        # Add user details
        rdata['orcid'] = user_info['orcid-identifier']
        rdata['user_name'] = (user_info['person']['name']
                              ['credit-name']['value'])

        if not is_multi:
            # And upload
            try:
                res = self._db.add_record(fd, rdata, vdata)
            except MagresDBError as e:
                return str(e), self.HTTP_400_BAD_REQUEST

            if not res.successful:
                return 'Uploading failed', self.HTTP_500_INTERNAL_SERVER_ERROR

            # Log the operation
            logdata = {
                'type': self.LOG_ADDRECORD,
                'mdbref': res.mdbref,
                'id': res.id
            }

            self._logger.log('Added record', rdata['orcid']['path'], logdata)
            ans = str(res.mdbref)

        else:
            # It's an archive!
            try:
                archive = MagresArchive(fd, record_data=rdata,
                                        version_data=vdata)
            except MagresArchiveError as e:
                return ('Invalid archive: {0}'.format(e),
                        self.HTTP_400_BAD_REQUEST)

            successful = []
            mdbrefs = []
            ids = []

            for f in archive.files():

                res = self._db.add_record(f.contents,
                                          f.record_data,
                                          f.version_data)

                successful.append(res.successful)
                if res.successful:
                    mdbrefs.append(res.mdbref)
                    ids.append(res.id)

            # How many were successful?
            n = sum(successful)
            N = len(successful)

            if n == 0:
                return 'Uploading failed', self.HTTP_500_INTERNAL_SERVER_ERROR
            elif n < N:
                return 'Uploaded {0}/{1} files from archive'.format(n, N)

            # Log the operation
            logdata = {
                'type': self.LOG_ADDARCHIVE,
                'mdbrefs': mdbrefs,
                'ids': ids
            }

            self._logger.log('Added archive', rdata['orcid']['path'], logdata)
            ans = json.dumps(mdbrefs)

        return ans, self.HTTP_200_OK

    def upload_version(self):

        # First, authenticate
        user_info = self.request_user_info()
        if 'error' in user_info:
            return user_info['error'], self.HTTP_401_UNAUTHORIZED

        # Get the data
        _, vdata = split_data(dict(request.values),
                              magresRecordSchemaUser,
                              magresVersionSchemaUser)

        fd = request.files.get('magres-file', None)
        r_id = request.values.get('_record_id')

        if r_id is None:
            return 'Missing record_id', self.HTTP_400_BAD_REQUEST

        # Update
        try:
            self._db.add_version(r_id, fd, vdata)
        except MagresDBError as e:
            return str(e), self.HTTP_500_INTERNAL_SERVER_ERROR

        return 'Success', self.HTTP_200_OK

    def hide_record(self):

        # Authenticate and check for admin status
        user_info = self.request_user_info(auth_admin=True)
        if 'error' in user_info:
            return user_info['error'], self.HTTP_401_UNAUTHORIZED

        r_id = request.values.get('_record_id')

        if r_id is None:
            return 'Missing record_id', self.HTTP_400_BAD_REQUEST

        res = self._db.set_visibility(r_id, False)

        if res:
            return 'Success', self.HTTP_200_OK
        else:
            return 'Unknown database error', self.HTTP_500_INTERNAL_SERVER_ERROR

    def search(self):
        query = request.json['search_spec']
        results = list(self._db.search_record(query))

        return json.dumps(results, default=str), self.HTTP_200_OK

    def get_record(self):
        mdbref = request.json['mdbref']
        query = [{'type': 'mdbref', 'args': {'mdbref': mdbref}}]
        results = list(self._db.search_record(query))

        n = len(results)

        if n == 1:
            return json.dumps(results[0], default=str), self.HTTP_200_OK
        elif n == 0:
            return '{}', self.HTTP_400_BAD_REQUEST
        elif n > 1:
            # What? Should not happen
            return '{}', self.HTTP_500_INTERNAL_SERVER_ERROR
            self._logger.log('Duplicate MDBREF found', 'N/A',
                             {'mdbref': mdbref})

    def get_magres(self):
        fs_id = request.args.get('magres_id')

        try:
            mfile = self._db.get_magres_file(fs_id)
        except MagresDBError:
            return 'File not found', self.HTTP_400_BAD_REQUEST
        except:
            return 'Invalid ID', self.HTTP_400_BAD_REQUEST

        resp = make_response(mfile)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = 'attachment'

        return resp, self.HTTP_200_OK
