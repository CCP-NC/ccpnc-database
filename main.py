#!/usr/bin/env python
"""
Serverside app providing support
to CCP-NC database, main file
"""

import os
import sys
import json
import inspect
from flask import Flask, Response, session, request, make_response
from orcid import OrcidConnection, OrcidError
from db_interface import (addMagresFile, databaseSearch,
                          getMagresFile, editMagresFile)
from db_schema import magresVersionOptionals

filepath = os.path.abspath(os.path.dirname(__file__))

app = Flask('ccpnc-database', static_url_path='',
            static_folder=os.path.join(filepath, "static"))
app.secret_key = open(os.path.join(filepath, 'secret',
                                   'secret.key')).read().strip()

orcid_details = json.load(open(os.path.join(filepath, 'secret',
                                            'orcid_details.json')))
orcid_link = OrcidConnection(orcid_details, 'https://orcid.org/')

# Response codes
HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_500_INTERNAL_SERVER_ERROR = 500

# Utilities


def user_info_auth():
    # Return user info if all tokens check out, otherwise raise OrcidError

    # First, check that the details are valid
    tk = orcid_link.get_tokens(session)
    client_at = request.values.get('access_token')
    client_id = request.values.get('orcid')

    if (tk is None or
            client_id != tk['orcid'] or
            client_at != tk['access_token']):
        raise OrcidError('Error: invalid login')

    return orcid_link.retrieve_info(session)


### APP ROUTES ###

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
    return 'Logged out', HTTP_200_OK


@app.route('/upload', methods=['POST'])
def upload():

    # Authenticate and retrieve user info
    try:
        user_info = user_info_auth()
    except OrcidError as e:
        # Something went wrong in the request itself
        return str(e), HTTP_401_UNAUTHORIZED

    # Compile everything
    try:

        # Obligatory values
        chemname = request.values.get('chemname')
        orcid = user_info['orcid-identifier']

        # Optional ones
        data = {
            k: request.values.get(k) for k in magresVersionOptionals
            if (request.values.get(k) is not None and
                len(request.values.get(k)) > 0)
        }

        success = addMagresFile(request.values.get('magres'),
                                chemname,
                                orcid,
                                data)

    except Exception as e:
        return (e.__class__.__name__ + ': ' + str(e),
                HTTP_500_INTERNAL_SERVER_ERROR)

    if success:
        return 'Success', HTTP_200_OK
    else:
        return 'Failed', HTTP_500_INTERNAL_SERVER_ERROR


@app.route('/edit', methods=['POST'])
def edit():

    # Authenticate and retrieve user info
    try:
        user_info = user_info_auth()
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
                                 data, request.values.get('magres'))

    except Exception as e:
        return (e.__class__.__name__ + ': ' + str(e),
                HTTP_500_INTERNAL_SERVER_ERROR)

    if success:
        return 'Success', HTTP_200_OK
    else:
        return 'Failed', HTTP_500_INTERNAL_SERVER_ERROR


@app.route('/search', methods=['POST'])
def search():

    try:
        results = databaseSearch(request.json['search_spec'])
    except ValueError as e:
        return ('ERROR: search parameters are wrong or incomplete '
                '({0})').format(e), HTTP_400_BAD_REQUEST

    return results, HTTP_200_OK


@app.route('/doc', methods=['GET'])
def get_doc():

    doc_id = request.args.get('id')

    resp = make_response(getMagresFile(doc_id))
    resp.headers['Content-Type'] = 'text/plain'
    resp.headers['Content-Disposition'] = 'attachment'

    return resp


@app.route('/optionals', methods=['GET'])
def get_optionals():

    # Return the optional arguments from the schema definition
    return json.dumps([
        {
            'short_name': k,
            'full_name': opt.full_name,
            'input_type': opt.input_type,
            'input_size': opt.input_size
        }
        for (k, opt) in magresVersionOptionals.items()
    ])


@app.route('/csvtemplate', methods=['GET'])
def get_csv():

    resp = make_response('filename,' +
                         ','.join(magresVersionOptionals.keys()))
    resp.headers['Content-Type'] = 'text/plain'
    resp.headers.set('Content-Disposition', 'attachment', filename='info.csv')

    return resp


if __name__ == '__main__':
    # Run locally; only launch this way when testing!

    # Authorise cross-origin for the sake of local testing
    from flask_cors import CORS
    CORS(app)

    app.config['SERVER_NAME'] = 'localhost:8000'
    app.run(port=8000, threaded=True)
