#!/usr/bin/env python
"""
Serverside app providing support
to CCP-NC database, main file
"""

import os
import json
from orcid import OrcidConnection
from flask import Flask, session
filepath = os.path.abspath(os.path.dirname(__file__))

app = Flask('ccpnc-database')
app.secret_key = open(os.path.join(filepath,
                                   'secret.key')).read().strip()

orcid_details = json.load(open(os.path.join(filepath,
                                            'orcid_details.json')))
orcid_link = OrcidConnection(orcid_details, 'https://orcid.org/')


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

if __name__ == '__main__':
    # Run locally; only launch this way when testing!

    # Authorise cross-origin for the sake of local testing
    from flask_cors import CORS
    CORS(app)

    app.config['SERVER_NAME'] = 'localhost:8080'
    app.run(port=8080, threaded=True)
