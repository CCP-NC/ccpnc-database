#!/usr/bin/env python
"""
Serverside app providing support
to CCP-NC database, main file
"""

import os
import sys
import json
import inspect
import ase
import flask
import soprano
from ccpncdb.server import MainServer

filepath = os.path.abspath(os.path.dirname(__file__))

# Create server app
serv = MainServer(filepath)

### APP ROUTES ###


@serv.app.route('/')
def root():
    return serv.send_static('index.html')


@serv.app.route('/cookies')
def cookiepol():
    return serv.send_static('cookies.html')


@serv.app.route('/logout')
def logout():
    return serv.logout()


@serv.app.route('/gettokens/', defaults={'code': None})
@serv.app.route('/gettokens/<code>')
def get_tokens(code):
    return serv.get_tokens(code)


@serv.app.route('/upload', methods=['POST'])
def upload():
    return serv.upload_record()


@serv.app.route('/edit', methods=['POST'])
def edit():
    return serv.upload_version()


@serv.app.route('/hide', methods=['POST'])
def hide():
    return serv.hide_record()


@serv.app.route('/search', methods=['POST'])
def search():
    return serv.search()


@serv.app.route('/get_record', methods=['POST'])
def get_record():
    return serv.get_record()


@serv.app.route('/get_magres', methods=['GET'])
def get_magres():
    return serv.get_magres()


@serv.app.route('/csvtemplate', methods=['GET'])
def get_csv():

    return serv.get_csv_template()


@serv.app.route('/pyversion', methods=['GET'])
def get_version():

    resp = """
<ul>
<li>Python:     {pyv}</li>
<li>ASE:        {asev}</li>
<li>Soprano:    {sprv}</li>
<li>Flask:      {flkv}</li>
</ul>
""".format(pyv=sys.version, asev=ase.__version__,
           sprv=soprano.__version__, flkv=flask.__version__)

    return resp


if __name__ == '__main__':
    # Run locally; only launch this way when testing!

    # Authorise cross-origin for the sake of local testing
    from flask_cors import CORS
    CORS(serv.app)

    serv.app.debug = True
    serv.app.config['SERVER_NAME'] = 'localhost:8000'
    serv.app.run(port=8000, threaded=True)
