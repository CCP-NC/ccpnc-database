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
    return serv.upload()


@serv.app.route('/search', methods=['POST'])
def search():
    return serv.search()

    # try:
    #     results = databaseSearch(request.json['search_spec'])
    # except ValueError as e:
    #     return ('ERROR: search parameters are wrong or incomplete '
    #             '({0})').format(e), HTTP_400_BAD_REQUEST

    # return results, HTTP_200_OK


"""

@app.route('/upload', methods=['POST'])
def upload():

    # Authenticate and retrieve user info
    try:
        user_info = user_info_auth(app.extensions['orcidlink'],
                                   request.values.get('access_token'),
                                   request.values.get('orcid'))
    except OrcidError as e:
        # Something went wrong in the request itself
        return str(e), HTTP_401_UNAUTHORIZED

    # Compile everything
    try:

        # Obligatory values
        chemname = request.values.get('chemname')
        chemform = request.values.get('chemform', '')
        license = request.values.get('license')
        orcid = user_info['orcid-identifier']

        # Optional ones
        data = {
            k: request.values.get(k) for k in magresVersionOptionals
            if (request.values.get(k) is not None and
                len(request.values.get(k)) > 0)
        }

        # Magres file
        fd = request.files['magres-file']

        if request.values.get('upload_multi', 'false') == 'true':
            succ_code, all_inds = addMagresArchive(fd,
                                                   chemname,
                                                   chemform,
                                                   license,
                                                   orcid,
                                                   data)
            success = (succ_code == 0)
        else:
            success = addMagresFile(fd,
                                    chemname,
                                    chemform,
                                    license,
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
        user_info = user_info_auth(app.extensions['orcidlink'],
                                   request.values.get('access_token'),
                                   request.values.get('orcid'))
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
                                 data, request.files.get('magres-file'))

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

    resp = make_response('filename,chemname,chemform,license,' +
                         ','.join(magresVersionOptionals.keys()))
    resp.headers['Content-Type'] = 'text/plain'
    resp.headers.set('Content-Disposition', 'attachment', filename='info.csv')

    return resp

"""

# @app.route('/pyversion', methods=['GET'])
# def get_version():

#     resp = """
# <ul>
# <li>Python:     {pyv}</li>
# <li>ASE:        {asev}</li>
# <li>Soprano:    {sprv}</li>
# <li>Flask:      {flkv}</li>
# </ul>
# """.format(pyv=sys.version, asev=ase.__version__,
#            sprv=soprano.__version__, flkv=flask.__version__)

#     print('Version')

#     return resp


if __name__ == '__main__':
    # Run locally; only launch this way when testing!

    # Authorise cross-origin for the sake of local testing
    from flask_cors import CORS
    CORS(serv.app)

    serv.app.debug = True
    serv.app.config['SERVER_NAME'] = 'localhost:8000'
    serv.app.run(port=8000, threaded=True)
