import os
import json
from datetime import timedelta
from flask import Flask, Response, session, request, make_response

from ccpncdb.config import Config
from ccpncdb.magresdb import MagresDB
from ccpncdb.orcid import OrcidConnection, NoOrcidTokens, OrcidError
from ccpncdb.utils import split_data
from ccpncdb.schemas import (magresRecordSchemaUser,
                             magresVersionSchemaUser)


class MainServer(object):

    # Response codes
    HTTP_200_OK = 200
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_500_INTERNAL_SERVER_ERROR = 500

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

        if not is_multi:
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

            # And upload
            res = self._db.add_record(fd, rdata, vdata)

            if not res.successful:
                return 'Uploading failed', self.HTTP_500_INTERNAL_SERVER_ERROR

        return 'Success', self.HTTP_200_OK

    def search(self):
        query = request.json['search_spec']
        results = self._db.search_record(query)

        print(results)
        for r in results:
            print(r)

        return '{}', self.HTTP_200_OK
