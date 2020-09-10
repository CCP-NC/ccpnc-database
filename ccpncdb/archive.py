import os
import csv
import zipfile
import tarfile
from io import StringIO
from collections import namedtuple
from ccpncdb.utils import get_schema_keys
from ccpncdb.schemas import magresRecordSchemaUser, magresVersionSchemaUser


MagresArchiveFile = namedtuple('MagresArchiveFile', ['name', 'contents',
                                                     'record_data',
                                                     'version_data'])


class MagresArchiveError(Exception):
    pass


class MagresArchive(object):

    VDATA_CASEINS_TAGS = ['extref_type', 'license']

    def __init__(self, archive, mode='r', record_data={}, version_data={}):
        """Load an archive of magres files with an optional .csv document
        to store file by file information"""

        self._default_record = record_data
        self._default_version = version_data

        self._magres_files = {}
        self._csv_file = {}

        self._mode = mode

        if mode == 'r':
            self.read(archive)
        elif mode == 'w':
            self._archive = archive

    def read(self, archive):
        _raw_files = {}

        try:
            with zipfile.ZipFile(archive) as z:
                for n in z.namelist():
                    name = os.path.basename(n)
                    if len(name) > 0:
                        with z.open(n) as f:
                            _raw_files[name] = f.read()
        except zipfile.BadZipfile:
            archive.seek(0)  # Clear
            try:
                with tarfile.open(fileobj=archive) as z:
                    for ti in z.getmembers():
                        if ti.isfile():
                            f = z.extractfile(ti)
                            name = os.path.basename(ti.name)
                            _raw_files[name] = f.read()
                            f.close()
            except tarfile.ReadError:
                raise RuntimeError(
                    'Uploaded archive file is not a valid zip or tar file.')

        # Now to split them
        for fname, file in _raw_files.items():
            ext = os.path.splitext(fname)[1]
            if ext == '.magres':
                self._magres_files[fname] = file.decode('UTF-8')
            elif ext == '.csv':
                csv_reader = csv.DictReader(StringIO(file.decode('UTF-8')))
                for row in csv_reader:
                    k, name = row.popitem(False)
                    if k != 'filename' or not (name in _raw_files):
                        raise MagresArchiveError('Invalid .csv file in '
                                                 'archive: all rows must'
                                                 ' include a valid filename as'
                                                 'first entry.')
                    # Remove empty entries
                    self._csv_file[name] = {key: val.strip()
                                            for key, val in row.items()
                                            if val.strip() != ''}

    def csvstr(self):
        """Make the CSV file into a string
        """

        # Find all keys
        keyset = set([])
        for f, d in self._csv_file.items():
            keyset = keyset.union(set(d.keys()))

        keyset = ['filename'] + sorted(list(keyset))

        # Write the header
        csvlines = [','.join(keyset)]

        for f, d in self._csv_file.items():
            row = [f] + [str(d.get(k, '')) for k in keyset[1:]]
            csvlines += [','.join(row)]

        return '\n'.join(csvlines)

    def write(self, ftype='zip'):

        if ftype == 'zip':
            zf = zipfile.ZipFile(self._archive, mode='w')

            # Create the CSV file
            csv = self.csvstr()
            zf.writestr('info.csv', csv)

            # Now write the magres files
            for name, contents in self._magres_files.items():
                zf.writestr(name, contents)

            zf.close()

    def add_file(self, name, contents, record_data={}, version_data={}):

        self._magres_files[name] = contents
        self._csv_file[name] = dict(record_data)
        self._csv_file[name].update(version_data)

    def files(self):
        """Return a generator for all files within the archive"""

        flist = sorted(list(self._magres_files.keys()))
        rkeys = get_schema_keys(magresRecordSchemaUser)
        vkeys = get_schema_keys(magresVersionSchemaUser)

        for f in flist:
            ftext = self._magres_files[f]
            cdata = self._csv_file.get(f, {})
            rdata = dict(self._default_record)
            rdata.update({k: v for k, v in cdata.items() if k in rkeys})
            vdata = dict(self._default_version)
            vdata.update({k: v for k, v in cdata.items() if k in vkeys})

            # Crude fix for tolerance of user behaviour            
            for tag in self.VDATA_CASEINS_TAGS:
                if tag in vdata:
                    vdata[tag] = vdata[tag].lower()


            yield MagresArchiveFile(f, ftext, rdata, vdata)

        return
