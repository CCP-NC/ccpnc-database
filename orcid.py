import re
import requests
from requests.exceptions import ConnectionError


class OrcidError(Exception):
    pass


class OrcidConnection:
    """ Provides an interface to connect with
    ORCID, given the relevant app data."""

    def __init__(self, details, login_url='https://orcid.org/',
                 api_url='https://pub.orcid.org/v2.0/'):

        self._details = details
        self._login_url = login_url
        self._api_url = api_url

    def retrieve_tokens(self, session, code):
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
            return None

        # Save them (if no error has occurred)
        rjson = r.json()
        if 'error' not in rjson:
            session['login_details'] = rjson

        return r.json()

    def get_tokens(self, session, code=None):
        # Retrieve existing tokens, or ask for new ones
        if 'login_details' in session and code is None:
            return session['login_details']
        elif code is not None:
            # Retrieve them
            return self.retrieve_tokens(session, code)
        else:
            # Something went wrong
            return None

    def delete_tokens(self, session):
        try:
            session.pop('login_details', None)
        except KeyError:
            pass

    def retrieve_info(self, session):

        tk = self.get_tokens(session)

        if tk is None:
            return None

        # Prepare a get request
        headers = {
            'Accept': 'application/json',
            'Authorization type': 'Bearer',
            'Access token': tk['access_token']
        }
        r = requests.get(self._api_url + tk['orcid'] + '/record',
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
        pass

    def retrieve_tokens(self, session, code):

        if code != '123456':
            raise RuntimeError('Invalid fake code! '
                               'The right fake code is 123456')

        fake_details = {
            'name': 'Johnny B. Goode',
            'access_token': 'XXX',
            'orcid': '0000-0000-0000-0000',
            'scope': '/authenticate'
        }

        session['login_details'] = fake_details

        return fake_details

    def retrieve_info(self, session):

        tk = self.get_tokens(session)

        if tk is None:
            return None

        return {'orcid-identifier': {
                'path': '0000-0000-0000-0000',
                'host': 'none',
                'uri': '0000-0000-0000-0000'
                }
                }
