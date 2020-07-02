import re
import os
import yaml
import requests
from requests.exceptions import ConnectionError


class NoOrcidTokens(Exception):
    # Raised only when login was made impossible by connection errors
    # or other issues
    pass


class OrcidError(Exception):
    pass


class OrcidConnection(object):
    """ Provides an interface to connect with
    ORCID, given the relevant app data."""

    # Path to banlist and admin list
    _banpath = os.path.join(os.path.split(
        __file__)[0], 'userlists/banlist.yaml')
    _adminpath = os.path.join(os.path.split(
        __file__)[0], 'userlists/adminlist.yaml')

    def __init__(self, details, session=None,
                 login_url='https://orcid.org/',
                 api_url='https://pub.orcid.org/v2.0/'):

        if session is None:
            # Use the global one
            from flask import session

        self._session = session
        self._details = details
        self._login_url = login_url
        self._api_url = api_url

    def is_banned(self, orcid):
        # Check if the given ORCID is in the banlist
        with open(self._banpath) as f:
            banlist = yaml.safe_load(f)
            banlist = [] if banlist is None else banlist

        return (orcid in banlist)

    def is_admin(self, orcid):
        # Check if the given ORCID is in the admin list
        with open(self._adminpath) as f:
            adminlist = yaml.safe_load(f)
            adminlist = [] if adminlist is None else adminlist

        return (orcid in adminlist)

    def request_public_tokens(self):
        # Get tokens from ORCID for a public API access
        headers = {'Accept': 'application/json'}
        payload = dict(self._details)
        payload.update({
            'grant_type': 'client_credentials',
            'scope': '/read-public',
        })

        try:
            r = requests.post(self._login_url + 'oauth/token',
                              data=payload, headers=headers)
        except ConnectionError:
            raise NoOrcidTokens('Connection to oauth/token failed')

        return r.json()

    def request_tokens(self, code):
        # Get tokens from ORCID given a request code
        headers = {'Accept': 'application/json'}
        payload = dict(self._details)
        payload.update({
            'grant_type': 'authorization_code',
            'code': code,
        })

        try:
            r = requests.post(self._login_url + 'oauth/token',
                              data=payload, headers=headers)
        except ConnectionError:
            raise NoOrcidTokens('Connection to oauth/token failed')

        # Save them (if no error has occurred, and if the user is authorised)
        rjson = r.json()
        if self.is_banned(rjson.get('orcid')):
            raise NoOrcidTokens('User has been banned from service')
        if self.is_admin(rjson.get('orcid')):
            rjson['admin'] = True

        if 'error' not in rjson:
            self._session.permanent = True
            self._session['login_details'] = rjson
        else:
            raise NoOrcidTokens('Connection to oauth/token returned error: ' +
                                rjson['error'])

    def get_tokens(self, code=None):
        # Retrieve existing tokens, or ask for new ones
        if code is not None:
            self.request_tokens(code)

        tk = self._session.get('login_details', None)

        if tk is None:
            raise NoOrcidTokens('No login details found')

        return tk

    def delete_tokens(self):
        self._session.pop('login_details', None)

    def authenticate(self, client_details, auth_admin=False):
        # Check client details vs. internally stored tokens

        tk = self.get_tokens()

        # Is the user banned?
        if self.is_banned(tk['orcid']):
            raise OrcidError('User has been banned')
            self.delete_tokens()

        try:
            auth = True
            for k in ('orcid', 'access_token'):
                auth = (auth and (client_details.get(k, None) == tk[k]))
        except KeyError:
            raise ValueError('Incomplete client details')

        if auth_admin:
            # Also check that the user is an admin
            auth = auth and self.is_admin(tk.get('orcid'))

        return auth

    def request_info(self, client_details, auth_admin=False):

        # Start by authenticating
        auth = self.authenticate(client_details, auth_admin=auth_admin)
        if not auth:
            raise OrcidError('Could not authenticate')

        tk = self.get_tokens()

        rdata = self.request_public_info(tk['orcid'], tk['access_token'])

        return rdata

    def request_public_info(self, orcid, token):
        # Request public info on a user, using the given access token

        headers = {
            'Accept': 'application/json',
            'Authorization type': 'Bearer',
            'Access token': token,
        }
        r = requests.get(self._api_url + orcid + '/record',
                         headers=headers)

        try:
            rdata = r.json()
        except AttributeError:
            raise OrcidError('Error: could not retrieve ORCID info')
        if 'error-code' in rdata:
            raise OrcidError(rdata['developer-message'])

        return rdata


class FakeOrcidConnection(OrcidConnection):

    """ Provides a fake interface imitating ORCID, for debugging purposes."""

    def __init__(self):
        self._session = {}

    def request_tokens(self, code):

        if code != '123456':
            raise NoOrcidTokens('Invalid fake code! '
                                'The right fake code is 123456')

        fake_details = {
            'name': 'Johnny B. Goode',
            'access_token': 'XXX',
            'orcid': '0000-0000-0000-0000',
            'scope': '/authenticate'
        }

        self._session['login_details'] = fake_details

        return fake_details

    def request_info(self, client_details, auth_admin=False):

        auth = self.authenticate(client_details, auth_admin=auth_admin)

        if not auth:
            raise OrcidError('Could not authenticate')

        return {'orcid-identifier': {
                'path': '0000-0000-0000-0000',
                'host': 'none',
                'uri': '0000-0000-0000-0000'
                },
                'person': {
                    'name': {
                        'credit-name': {
                            'value': 'John Doe'
                        }
                    }
        }
        }
