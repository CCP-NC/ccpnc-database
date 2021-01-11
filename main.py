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
app = serv.app

### APP ROUTES ###


@app.route('/')
def root():
    return serv.send_static('index.html')


@app.route('/cookies')
def cookiepol():
    return serv.send_static('cookies.html')


@app.route('/logout')
def logout():
    return serv.logout()


@app.route('/gettokens/', defaults={'code': None})
@app.route('/gettokens/<code>')
def get_tokens(code):
    return serv.get_tokens(code)


@app.route('/upload', methods=['POST'])
def upload():
    return serv.upload_record()


@app.route('/edit', methods=['POST'])
def edit():
    return serv.upload_version()


@app.route('/hide', methods=['POST'])
def hide():
    return serv.hide_record()


@app.route('/search', methods=['POST'])
def search():
    return serv.search()


@app.route('/get_record', methods=['POST'])
def get_record():
    return serv.get_record()


@app.route('/get_magres', methods=['GET'])
def get_magres():
    return serv.get_magres()


@app.route('/get_csv', methods=['GET'])
def get_csv():
    return serv.get_csv()


@app.route('/csvtemplate', methods=['GET'])
def get_csv_template():
    return serv.get_csv_template()


@app.route('/sendmail', methods=['POST'])
def send_mail():
    return serv.send_mail()


@app.route('/pyversion', methods=['GET'])
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
    CORS(app)

    app.debug = True
    app.config['SERVER_NAME'] = 'localhost:8000'
    app.run(port=8000, threaded=True)
