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
        self._app.secret_key = open(os.path.join(path, 'secret',
                                                 'secret.key')).read().strip()

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
        self._db = MagresDB(client=self._client)
        self._logger = Logger(client=self._client)

    @property
    def app(self):
        return self._app

    def send_static(self, url):
        return self._app.send_static_file(url)

    def request_user_info(self):

        client_details = {
            'orcid': request.values.get('_auth_id', None),
            'access_token': request.values.get('_auth_tk', None)
        }

        try:
            rinfo = self._orcid.request_info(client_details)
        except OrcidError:
            return None

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

    def upload(self):

        # First, authenticate
        user_info = self.request_user_info()
        if user_info is None:
            return 'Failed', self.HTTP_401_UNAUTHORIZED

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

        return 'Success', self.HTTP_200_OK

    def upload_version(self):
        
        # First, authenticate
        user_info = self.request_user_info()
        if user_info is None:
            return 'Failed', self.HTTP_401_UNAUTHORIZED

        fd = request.files.get('magres-file', None)

        print(request.values)

        """# Authenticate and retrieve user info
            try:
                user_info = user_info_auth(app.extensions['orcidlink'],
                                           request.values.get('access_token'),
                                           request.values.get('orcid'))
            except OrcidError as e:
                # Something went wrong in the request itself
                return str(e), HTTP_401_UNAUTHORIZED

            # Compile everything
            try:
                # Obligatory values
                index_id = request.values.get('index_id')
                orcid = user_info['orcid-identifier']

                # Optional ones
                data = {
                    k: request.values.get(k) for k in magresVersionOptionals
                    if (request.values.get(k) is not None and
                        len(request.values.get(k)) > 0)
                }

                success = editMagresFile(index_id, orcid,
                                         data, request.files.get('magres-file'))

            except Exception as e:
                return (e.__class__.__name__ + ': ' + str(e),
                        HTTP_500_INTERNAL_SERVER_ERROR)

            if success:
                return 'Success', HTTP_200_OK
            else:
                return 'Failed', HTTP_500_INTERNAL_SERVER_ERROR


        [description]
        """

    def search(self):
        query = request.json['search_spec']
        results = list(self._db.search_record(query))

        return json.dumps(results, default=str), self.HTTP_200_OK
