import re
from datetime import datetime
from ase.io.magres import read_magres
from schema import Schema, And, Optional

"""A schema for entries to be uploaded to the Database.
This currently does not include the cross-referencing IDs, as they are 
obligatory but enforced by the uploading process itself."""

orcid_path_re = re.compile('[0-9]{4}-'*3+'[0-9]{3}[0-9X]{1}\Z')
csd_digits_re = re.compile('[0-9]{2}\Z')

orcidSchema = Schema({
    'path': orcid_path_re.match,
    'host': basestring,
    'uri': orcid_path_re.search,
})

magresVersionSchema = Schema({
    'magresFilesID': basestring,
    'date': datetime,
    Optional('doi', default=''): basestring,
    Optional('notes'): basestring,
    Optional('csd-ref'): {
        'refcode': And(basestring, lambda s: len(s) == 6),
        Optional('digits'): csd_digits_re.match
    }
})

magresMetadataSchema = Schema({
    'chemname': And(basestring, len),
    'orcid': orcidSchema,
    'version_history': [magresVersionSchema]
})

magresIndexSchema = Schema({
    'chemname': And(basestring, len),
    'orcid': orcidSchema,
    'metadataID': str,
    'latest_version': magresVersionSchema,
    'values': [{
        'species': basestring,
        'iso': [float],
    }],
    'formula': [{'species': str,
                 'n': int}]

})

# Convenient to keep a list of optional version keys
opt_re = re.compile('Optional\(\'([a-zA-Z\-]+)\'\)')
magresVersionOptFields = [opt_re.match(str(k)).groups()[0]
                          for k in magresVersionSchema._schema.keys()
                          if opt_re.match(str(k)) != None]
