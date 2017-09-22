#!/usr/bin/env python
"""
Serverside app providing support
to CCP-NC database, main file
"""

import os
import json
from orcid import OrcidConnection
from flask import Flask, session, request
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

@app.route('/getinfo')
def getinfo():
    return json.dumps(orcid_link.retrieve_info(session))

@app.route('/upload', methods=['POST'])
def upload():
    print request.form    
    print request.files
    return json.dumps(request.form)

if __name__ == '__main__':
    # Run locally; only launch this way when testing!

    # Authorise cross-origin for the sake of local testing
    from flask_cors import CORS
    CORS(app)

    app.config['SERVER_NAME'] = 'localhost:8000'
    app.run(port=8000, threaded=True)

