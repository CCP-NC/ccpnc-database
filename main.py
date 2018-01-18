#!/usr/bin/env python
"""
Serverside app providing support
to CCP-NC database, main file
"""

import os
import json
import inspect
from flask import Flask, session, request
from orcid import OrcidConnection, OrcidError
from db_interface import addMagresFile, databaseSearch

filepath = os.path.abspath(os.path.dirname(__file__))

app = Flask('ccpnc-database', static_url_path='',static_folder = os.path.join(filepath,"static"))
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
    try:
        user_info = orcid_link.retrieve_info(session)
    except OrcidError as e:
        # Something went wrong in the request itself
        return str(e)

    # Compile everything
    try:

        # Obligatory values
        file_entry = {
            'chemname': request.values.get('chemname'),
            'orcid': user_info['orcid-identifier'],
        }

        # Optional ones
        file_entry.update({
            k: request.values.get(k) for k in ('doi', 'notes')
            if (request.values.get(k) is not None and
                len(request.values.get(k)) > 0)
        })

        success = addMagresFile(request.values.get('magres'), file_entry)

    except Exception as e:
        return e.__class__.__name__ + ': ' + str(e)

    ### HERE GOES THE CODE TO UPLOAD TO THE DATABASE ###

    return 'Success' if success else 'Failed'


@app.route('/search', methods=['POST'])
def search():

    try:
        results = databaseSearch(request.json['search_spec'])
    except ValueError as e:
        return ('ERROR: search parameters are wrong or incomplete '
                '({0})').format(e)

    return results


if __name__ == '__main__':
    # Run locally; only launch this way when testing!

    # Authorise cross-origin for the sake of local testing
    from flask_cors import CORS
    CORS(app)

    app.config['SERVER_NAME'] = 'localhost:8000'
    app.run(port=8000, threaded=True)
