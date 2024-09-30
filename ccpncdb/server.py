import io
import os
import csv
import json
from datetime import timedelta
from flask import Flask, Response, session, request, make_response
from flask_mail import Mail, Message
import zipfile


from ccpncdb.config import Config
from ccpncdb.magresdb import MagresDB, MagresDBError
from ccpncdb.log import Logger
from ccpncdb.orcid import OrcidConnection, NoOrcidTokens, OrcidError
from ccpncdb.utils import split_data, get_name_from_orcid, get_schema_keys
from ccpncdb.schemas import (magresRecordSchemaUser,
                             magresVersionSchemaUser, csvProperties)
from ccpncdb.archive import MagresArchive, MagresArchiveError
from ccpncdb.metadataexport import MetadataExport


def make_csv_response(for_uploading=False):
    response = Response()
    props = list(csvProperties)
    # If it's for uploading, add filename
    if for_uploading:
        props = ['filename'] + props
    writer = csv.DictWriter(response.stream, props,
                            extrasaction='ignore')
    writer.writeheader()

    return response, writer


class MainServer(object):

    # Response codes
    HTTP_200_OK = 200
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_500_INTERNAL_SERVER_ERROR = 500

    # Log types
    LOG_ADDRECORD = 0
    LOG_ADDARCHIVE = 1
    LOG_ADDVERSION = 2

    def __init__(self, path='', db=None): #db is None for production/development server, recieves db object for CI testing

        self._path = path
        self._static_folder = os.path.join(path, 'static')
        self._config_folder = os.path.join(path, 'config')
        self.metadata_exporter = MetadataExport()

        self._app = Flask('ccpnc-database', static_url_path='',
                          static_folder=self._static_folder)
        # Load secret key
        with open(os.path.join(path, 'secret', 'secret.key')) as secret:
            self._app.secret_key = secret.read().strip()

        # Set up cookie, duration: one month
        self._app.config['SESSION_COOKIE_NAME'] = 'CCPNCDBLOGIN'
        self._app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

        with open(os.path.join(path, 'secret',
                               'orcid_details.json')) as f:
            self._orcid_details = json.load(f)

        if not hasattr(self._app, 'extensions'):
            self._app.extensions = {}
        self._app.extensions['orcidlink'] = OrcidConnection(
            self._orcid_details, session)
        self._orcid = self._app.extensions['orcidlink']

        if db is None:
            self._config = Config(os.path.join(self._config_folder,
                                           'config.json'))
            self._client = self._config.client()
            self._dbname = self._config.db_name
            self._db = MagresDB(client=self._client, dbname=self._dbname)
            self._logger = Logger(client=self._client, dbname=self._dbname)
        else:
            self._db = db

        # Load mail config
        with open(os.path.join(self._config_folder, 'smtpconfig.json')) as f:
            self._app.config.update(json.load(f))

        self._mail = Mail(self._app)

    @property
    def app(self):
        return self._app

    @property
    def orcid(self):
        return self._orcid

    @orcid.setter
    def orcid(self, val):
        self._orcid = val
        self._app.extensions['orcidlink'] = val

    def send_static(self, url):
        return self._app.send_static_file(url)

    def request_user_info(self, auth_admin=False):

        client_details = {
            'orcid': request.values.get('_auth_id', None),
            'access_token': request.values.get('_auth_tk', None)
        }

        try:
            rinfo = self._orcid.request_info(client_details,
                                             auth_admin=auth_admin)
        except OrcidError as e:
            return {'error': str(e)}

        return rinfo

    def logout(self):
        self._orcid.delete_tokens()
        return 'Logged out', self.HTTP_200_OK

    def get_tokens(self, code=None):
        try:
            tk = self._orcid.get_tokens(code)
        except NoOrcidTokens as e:
            return str(e), self.HTTP_401_UNAUTHORIZED

        return json.dumps(tk), self.HTTP_200_OK

    def upload_record(self):

        # First, authenticate
        user_info = self.request_user_info()
        if 'error' in user_info:
            return user_info['error'], self.HTTP_401_UNAUTHORIZED

        # Upload: single, or multiple?
        is_multi = request.values.get('_upload_multi', 'false') == 'true'

        # Fetch the actual magres file
        fd = request.files['magres-file']

        # Now extract the record information
        rdata, vdata = split_data(request.values.to_dict(),
                                  magresRecordSchemaUser,
                                  magresVersionSchemaUser)

        # Add user details
        rdata['orcid'] = user_info['orcid-identifier']
        rdata['user_name'] = get_name_from_orcid(user_info)

        if not is_multi:
            # And upload
            try:
                res = self._db.add_record(fd, rdata, vdata)
            except MagresDBError as e:
                return str(e), self.HTTP_400_BAD_REQUEST

            if not res.successful:
                return 'Uploading failed', self.HTTP_500_INTERNAL_SERVER_ERROR

            # Log the operation
            logdata = {
                'type': self.LOG_ADDRECORD,
                'mdbref': res.mdbref,
                'id': res.id
            }

            self._logger.log('Added record', rdata['orcid']['path'], logdata)
            ans = str(res.mdbref)

        else:

            try:
                results = self._db.add_archive(fd, rdata, vdata)
            except Exception as e:
                return str(e), self.HTTP_400_BAD_REQUEST

            successful = []
            failed = []
            mdbrefs = []
            ids = []

            for name, res in results.items():

                if (res is None) or not res.successful:
                    failed.append(f.name)
                    successful.append(False)
                else:
                    mdbrefs.append(res.mdbref)
                    ids.append(res.id)
                    successful.append(True)

            # Log the operation
            logdata = {
                'type': self.LOG_ADDARCHIVE,
                'mdbrefs': mdbrefs,
                'ids': ids
            }

            # How many were successful?
            n = sum(successful)
            N = len(successful)

            ans = {}
            ans['success'] = (n > 0) + (n == N)
            ans['uploaded'] = '{0}/{1}'.format(n, N)
            ans['mdbrefs'] = mdbrefs
            ans['failed'] = failed

            self._logger.log('Added archive', rdata['orcid']['path'], logdata)
            ans = json.dumps(ans)

        return ans, self.HTTP_200_OK

    def upload_version(self):

        # First, authenticate
        user_info = self.request_user_info()
        if 'error' in user_info:
            return user_info['error'], self.HTTP_401_UNAUTHORIZED

        # Get the data
        _, vdata = split_data(request.values.to_dict(),
                              magresRecordSchemaUser,
                              magresVersionSchemaUser)

        fd = request.files.get('magres-file', None)
        r_id = request.values.get('_record_id')

        if r_id is None:
            return 'Missing record_id', self.HTTP_400_BAD_REQUEST

        # Update
        try:
            self._db.add_version(r_id, fd, vdata)
        except MagresDBError as e:
            return str(e), self.HTTP_500_INTERNAL_SERVER_ERROR

        return 'Success', self.HTTP_200_OK

    def hide_record(self):

        # Authenticate and check for admin status
        user_info = self.request_user_info(auth_admin=True)
        if 'error' in user_info:
            return user_info['error'], self.HTTP_401_UNAUTHORIZED

        r_id = request.values.get('_record_id')

        if r_id is None:
            return 'Missing record_id', self.HTTP_400_BAD_REQUEST

        res = self._db.set_visibility(r_id, False)

        if res:
            return 'Success', self.HTTP_200_OK
        else:
            return ('Unknown database error',
                    self.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def unpack_file(self, file):
        """
        Unpacks the file information from the given dictionary.

        Args:
            file (dict): The dictionary containing the file information.

        Returns:
            tuple: A tuple containing the file ID, filename, and database record JSON.
        """
        file_id = file['fileID'] #Magres file ID
        filename = file['filename'] #Magres file name for download
        db_record_json = file['jsonData'] #JSON data for cleanup
        version_num = file['version'] #Version number for metadata

        return file_id, filename, db_record_json, version_num

    def json_metadata_prepare(self, json_data, fs_id, version_num):
        """
        Prepare the JSON metadata for export to either an archive in bulk downloads or a standalone JSON file 
        download.

        Args:
            json_data (dict): The JSON data to be prepared.
            fs_id (str): The ID of the corresponding Magres file.
            is_archive (bool, optional): Indicates if the data is for an archive. Defaults to False.

        Returns:
            dict: The prepared JSON metadata.

        Comments:
            - This function prepares the JSON metadata for export by performing clearance and cleanup operations.
            - The `json_data` parameter should be a dictionary containing the JSON data to be prepared.
            - The `fs_id` parameter should be a string representing a Magres File ID.
            - The `is_archive` parameter is an optional boolean flag indicating if the data is for an archive.
              It defaults to False if not provided, this option is used when individual JSOn metadata is downloaded
              for Magres database records.
            - The function returns a dictionary containing the prepared JSON metadata.
        """
        json_cleaned = self.metadata_exporter.metadata_clearance(json_data) #Remove redundant metadata
        json_final = self.metadata_exporter.metadata_cleanup(json_cleaned, version_num, fs_id) #Clean up - include relevant file version metadata

        return json_final
    
    def download_selection_json(self):
        """
        Downloads the selected JSON file from the server.

        Returns:
            - If the file is valid:
                - A response object containing the JSON data.
                - HTTP status code 200 (OK).
            - If the file is invalid:
                - An error message indicating the invalid file content.
                - HTTP status code 400 (Bad Request).
            - If there is an error retrieving the file:
                - An error message indicating the file retrieval error.
                - HTTP status code 400 (Bad Request).
        """
        file = request.json['files'][0] #Get the selected file from the request
        fs_id, filename, json_data, version_num = self.unpack_file(file) #unpack file information

        try:
            mfile = self._db.get_magres_file(fs_id) #Retrieve Magres file from database
            if isinstance(mfile, bytes): #Check if the file content is valid
                # Preparing to write metadata to JSON file
                json_final = self.json_metadata_prepare(json_data, fs_id, version_num)
                json_str = json.dumps(json_final, indent=1)

                # Create a response object with the JSON data
                response = Response(json_str, mimetype='application/json')
                response.headers['Content-Disposition'] = f'inline; filename={filename}.json'
                return response, self.HTTP_200_OK #Return the response object and HTTP status code 200 (OK)
            else: # Log error and return invalid file content message
                self._logger.log('Error: Invalid file content', json_data['orcid']['path'], {'Magres_id': fs_id})
                return f"Invalid file content for {fs_id}: {mfile}", self.HTTP_400_BAD_REQUEST
            
        except MagresDBError as e: # Log error and return file retrieval error message
            self._logger.log(f"Error retrieving file: {e}", json_data['orcid']['path'], {'Magres_id': fs_id})
            return f"Error retrieving file {fs_id}: {e}", self.HTTP_400_BAD_REQUEST
    
    def download_selection_zip(self):
        """
        Downloads a selection of Magres files as a zip archive with a JSOn metadata file and a human-readable 
        CSV metadata file included.
        
        Returns:
            A Response object containing the zip archive as the response content and the HTTP status code.
        
        Comments:
            - This function allows the user to download a selection of Magres files as a zip archive.
            - The files to be included in the archive are specified in the request JSON.
            - The function creates a zip archive in memory and adds each selected file to the archive.
            - It also prepares and includes metadata for each file in the archive.
            - The function returns a Response object with the zip archive as the response content.
            - The HTTP status code indicates the success or failure of the operation.
        """
        
        files = request.json['files'] #Get the list of files from the request
        archive = io.BytesIO() #Create an in-memory byte stream for the zip archive
        json_metadata = {} #Create an empty dictionary to store the JSON metadata for each file

        # Create a CSV file in memory
        csv_file = io.StringIO()
        props = ['filename'] + list(csvProperties) #Include filename in the CSV file header
        writer = csv.DictWriter(csv_file, props, extrasaction='ignore') # Create a CSV writer object
        writer.writeheader() # Write the header to the CSV file

        with zipfile.ZipFile(archive, 'w') as zipf:
            for file in files: # loop through the selected files
                fs_id, filename, json_data, version_num = self.unpack_file(file) #Unpack file information
                try:
                    mfile = self._db.get_magres_file(fs_id) #Retrieve Magres file from database
                    if isinstance(mfile, bytes): #Check if the file content is valid
                        zipf.writestr(f"{filename}.magres", mfile)
                    else: #Log error and continue to the next file
                        self._logger.log('Error: Invalid file content', 
                                         json_data['orcid']['path'], 
                                         {'Magres_id': fs_id})
                        continue

                    # Preparing to write metadata to JSON file
                    json_final = self.json_metadata_prepare(json_data, fs_id, version_num) #Prepare metadata for export
                    json_metadata[f"{filename}.magres metadata"] = json_final  #Add metadata to the JSON metadata dictionary with filename as key

                    #Preparing to write metadata to CSV file
                    json_csv = json_final.copy() #Create a shallow copy of the JSON metadata
                    json_csv['filename'] = filename #Add the filename to the JSON metadata
                    csv_version = json_csv['last_version'] #Get the last version metadata
                    row = dict(json_csv, **csv_version) #Combine the record and version metadata
                    writer.writerow(row) #Write the metadata to the CSV file, as per the schema

                except MagresDBError as e:
                    # Log error and continue to the next file
                    self._logger.log(f"Error retrieving file: {e}", 
                                     json_data['orcid']['path'], 
                                     {'Magres_id': fs_id})
                    continue

            json_metadata_str = json.dumps(json_metadata, indent=1) #Convert the JSON metadata dictionary to a string
            zipf.writestr("Magres_metadata.json", json_metadata_str) #Write the JSON metadata to the archive

            # Move to the CSV file next
            csv_file.seek(0) #Move the cursor to the beginning of the file
            zipf.writestr("Magres_metadata.csv", csv_file.getvalue()) #Write the CSV file to the archive
        
        archive.seek(0) #Move the cursor to the beginning of the archive

        # Return the zip archive as a response object
        return Response(archive.getvalue(),
                        mimetype='application/zip',
                        headers={'Content-Disposition': 'attachment;filename=selected_files.zip'}), self.HTTP_200_OK

    def search(self):

        query = request.json['search_spec']
        try:
            results = list(self._db.search_record(query))
        except MagresDBError as e:
            results = []

        return json.dumps(results, default=str), self.HTTP_200_OK

    def get_record(self):
        mdbref = request.json['mdbref']
        query = [{'type': 'mdbref', 'args': {'mdbref': mdbref}, 'boolean': False}]
        results = list(self._db.search_record(query))

        n = len(results)

        if n == 1:
            return json.dumps(results[0], default=str), self.HTTP_200_OK
        elif n == 0:
            return '{}', self.HTTP_400_BAD_REQUEST
        elif n > 1:
            # What? Should not happen
            return '{}', self.HTTP_500_INTERNAL_SERVER_ERROR
            self._logger.log('Duplicate MDBREF found', 'N/A',
                             {'mdbref': mdbref})

    def get_csv(self):

        oid = request.args.get('oid')
        v = int(request.args.get('v'))
        record = self._db.get_record(oid)
        version = record['version_history'][v]
        row = dict(record, **version)

        # Form a csv file
        resp, w = make_csv_response()
        w.writerow(row)

        return resp, self.HTTP_200_OK

    def get_csv_template(self):

        resp, _ = make_csv_response(True)

        return resp, self.HTTP_200_OK

    def get_magres(self):
        fs_id = request.args.get('magres_id')

        try:
            mfile = self._db.get_magres_file(fs_id)
        except MagresDBError:
            return 'File not found', self.HTTP_400_BAD_REQUEST
        except:
            return 'Invalid ID', self.HTTP_400_BAD_REQUEST

        resp = make_response(mfile)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = 'attachment'

        return resp, self.HTTP_200_OK

    def get_magres_archive(self):

        raise NotImplementedError()

        fs_ids = request.json.get('magres_id_list')

        bio = io.BytesIO()
        arch = MagresArchive(bio, mode='w')

        for fs_id in fs_ids:
            try:
                mfile = self._db.get_magres_file(fs_id)
            except MagresDBError as e:
                continue

        return 'OK', self.HTTP_200_OK

    def send_mail(self):

        sender = request.values.get('_sender', '')
        title = request.values.get('_title', '')
        body = request.values.get('_body', '')

        if sender == '' or body == '':
            return 'Missing sender or message body', self.HTTP_400_BAD_REQUEST
        if title == '':
            # Just do a standard one...
            title = 'Untitled Message'

        email = Message(title, sender=sender, recipients=['ccpnc@gmail.com'])
        email.body = body

        try:
            self._mail.send(email)
        except Exception as e:
            return str(e), self.HTTP_500_INTERNAL_SERVER_ERROR

        return 'Message sent', self.HTTP_200_OK
