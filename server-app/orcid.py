from requests import post
from requests.exceptions import ConnectionError


class OrcidConnection:
    """ Provides an interface to connect with
    ORCID, given the relevant app data."""

    def __init__(self, details, orcid_url='https://orcid.org/'):

        self._details = details
        self._url = orcid_url

    def retrieve_tokens(self,session, code):
        # Get tokens from ORCID given a request code
        headers = {'Accept': 'application/json'}
        payload = dict(self._details)
        payload.update({
            'grant_type': 'authorization_code',
            'code': code,
        })

        try:
            r = post(self._url + 'oauth/token',
                     data=payload, headers=headers)
        except ConnectionError:
            return None

        # Save them (if no error has occurred)
        rjson = r.json()
        if 'error' not in rjson:
            print rjson
            session['login_details'] = rjson
            print session['login_details']

        return r.json()

    def get_tokens(self, session, code=None):
        # Retrieve existing tokens, or ask for new ones
        if 'login_details' in session and code is None:
            print session['login_details']
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
