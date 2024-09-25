import mongomock
# from mongomock.gridfs import enable_gridfs_integration
import gridfs
from unittest import mock
from bson.objectid import ObjectId

class MockGridFile:
    def __init__(self, data):
        # Store data as bytes. If data is a string, encode it to bytes using UTF-8.
        self.data = data.encode('utf-8') if isinstance(data, str) else data

    def read(self):
        # Return the stored data.
        return self.data

class MockGridFS:
    def __init__(self, database, collection='fs'):
        # Initialize with a reference to the database and collection name.
        self.database = database
        self.collection = collection
        # Dictionary to store files with their ObjectId as keys.
        self.files = {}

    def put(self, data, **kwargs):
        # Generate a new ObjectId for the file.
        file_id = ObjectId()
        # Store the data in the files dictionary.
        self.files[file_id] = data
        # Return the ObjectId of the stored file.
        return file_id

    def get(self, file_id):
        # Retrieve the data associated with the given file_id.
        data = self.files.get(file_id)
        # Return a MockGridFile instance containing the data.
        return MockGridFile(data)

class MockGridIn:
    def __init__(self, database, collection='fs'):
        # Initialize with a reference to the database and collection name.
        self.database = database
        self.collection = collection

class MockGridOut:
    def __init__(self, database, collection='fs'):
        # Initialize with a reference to the database and collection name.
        self.database = database
        self.collection = collection

def enable_gridfs_integration():
    # Patch the gridfs.GridFS class to use the MockGridFS class.
    mock.patch('gridfs.GridFS', MockGridFS).start()
    # Patch the gridfs.GridIn class to use the MockGridIn class.
    mock.patch('gridfs.GridIn', MockGridIn).start()
    # Patch the gridfs.GridOut class to use the MockGridOut class.
    mock.patch('gridfs.GridOut', MockGridOut).start()