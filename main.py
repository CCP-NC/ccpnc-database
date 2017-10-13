#!/usr/bin/env python
"""
Serverside app providing support
to CCP-NC database, main file
"""

import os
import json
import inspect
from orcid import OrcidConnection
from flask import Flask, session, request
from db_interface import addMagresFile, databaseSearch

filepath = os.path.abspath(os.path.dirname(__file__))

app = Flask('ccpnc-database', static_url_path='')
app.secret_key = open(os.path.join(filepath, 'secret',
                                   'secret.key')).read().strip()

orcid_details = json.load(open(os.path.join(filepath, 'secret',
                                            'orcid_details.json')))
orcid_link = OrcidConnection(orcid_details, 'https://orcid.org/')


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/gettokens/', defaults={'code': None})
@app.route('/gettokens/<code>')
def get_tokens(code):
    tk = orcid_link.get_tokens(session, code)
    # If they are None, return null
    if tk is None:
        return 'null'
    else:
        return json.dumps(tk)


@app.route('/logout')
def delete_tokens():
    orcid_link.delete_tokens(session)
    return 'Logged out'


@app.route('/upload', methods=['POST'])
def upload():

    # First, check that the details are valid
    tk = orcid_link.get_tokens(session)
    client_at = request.values.get('access_token')
    client_id = request.values.get('orcid')

    if (tk is None or
            client_id != tk['orcid'] or
            client_at != tk['access_token']):
        return 'Error: invalid login'

    # Ok, so pick the rest of the information
    user_info = orcid_link.retrieve_info(session)

    if user_info is None:
        # Should never happen unless ORCID is down...
        return 'Error: could not retrieve ORCID info'

    # Compile everything
    file_entry = {
        'chemname': request.values.get('chemname'),
        'doi': request.values.get('doi'),
        'notes': request.values.get('notes'),
        'user_id': client_id,
        'user_info': user_info,
    }

    try:
        success = addMagresFile(request.values.get('magres'), file_entry)
    except Exception as e:
        return str(e)

    ### HERE GOES THE CODE TO UPLOAD TO THE DATABASE ###

    return 'Success' if success else 'Failed'


@app.route('/search', methods=['POST'])
def search():

    try:
        results = databaseSearch(request.json['search_spec'])
    except ValueError:
        return 'ERROR: search parameters are wrong or incomplete'

    return results


if __name__ == '__main__':
    # Run locally; only launch this way when testing!

    # Authorise cross-origin for the sake of local testing
    from flask_cors import CORS
    CORS(app)

    app.config['SERVER_NAME'] = 'localhost:8000'
    app.run(port=8000, threaded=True)
