import re
from datetime import datetime
from collections import namedtuple
from ase.io.magres import read_magres
from schema import Schema, And, Optional

"""Data schemas for entries to be uploaded to the Database."""

orcid_path_re = re.compile('[0-9]{4}-'*3+'[0-9]{3}[0-9X]{1}\Z')
csd_digits_re = re.compile('[0-9]{2}\Z')

# Optional arguments for each magres version. These are useful also
# client-side so we store them in their own definitions

OptVArg = namedtuple('OptVArg', ['full_name', 'validator',
                                 'input_type', 'input_size'])

magresVersionArguments = {
    'magresFilesID': basestring,
    'date': datetime
}

magresVersionOptionals = {
    'doi': OptVArg('DOI', basestring,
                   'text',
                   '35'),
    'notes': OptVArg('Notes', basestring,
                     'textarea',
                     None),
    'csd-ref': OptVArg('CSD reference', {
        'refcode': And(basestring, lambda s: len(s) == 6),
        Optional('digits'): csd_digits_re.match
    },
        'text',
        50)
}

magresVersionArguments.update({
    Optional(k): opt.validator
    for (k, opt) in magresVersionOptionals.items()
})

# Schemas

orcidSchema = Schema({
    'path': orcid_path_re.match,
    'host': basestring,
    'uri': orcid_path_re.search,
})

magresVersionSchema = Schema(magresVersionArguments)

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
