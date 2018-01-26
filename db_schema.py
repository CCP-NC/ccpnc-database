import re
from ase.io.magres import read_magres
from schema import Schema, And, Optional

"""A schema for entries to be uploaded to the Database.
This currently does not include the cross-referencing IDs, as they are 
obligatory but enforced by the uploading process itself."""

orcid_path_re = re.compile('[0-9]{4}-'*3+'[0-9]{3}[0-9X]{1}\Z')
csd_digits_re = re.compile('[0-9]{2}\Z')

magresDataSchema = Schema({
    'chemname': And(basestring, len),
    'orcid': {
        'path': orcid_path_re.match,
        'host': basestring,
        'uri': orcid_path_re.search,
    },
    'values': [{
        'species': basestring,
        'iso': [float],
    }],
    Optional('doi'): basestring,
    Optional('notes'): basestring,
    Optional('metadata'): dict,
    Optional('csd-ref'): {
        'refcode': And(basestring, lambda s: len(s) == 6),
        Optional('digits'): csd_digits_re.match
    }
})

orcidSchema = Schema({
    'path': orcid_path_re.match,
    'host': basestring,
    'uri': orcid_path_re.search,
})

magresVersionSchema = Schema({
    'magresFilesID': basestring,
    Optional('doi'): basestring,
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
    'values': [{
        'species': basestring,
        'iso': [float],
    }],
    'formula': [{'species': str,
                 'n': int}]
                 
})
