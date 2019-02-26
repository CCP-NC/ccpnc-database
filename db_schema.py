from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
from datetime import datetime
from collections import namedtuple, OrderedDict
from ase.io.magres import read_magres
from schema import Schema, And, Optional

# Python3 compatibility
try:
  basestring
except NameError:
  basestring = str

"""Data schemas for entries to be uploaded to the Database."""

orcid_path_re = re.compile('[0-9]{4}-'*3+r'[0-9]{3}[0-9X]{1}\Z')
csd_refcode_re = re.compile(r'[A-Z]{6}([0-9]{2})?\Z')
csd_number_re = re.compile(r'[0-9]{6,7}\Z')

# Optional arguments for each magres version. These are useful also
# client-side so we store them in their own definitions

OptVArg = namedtuple('OptVArg', ['full_name', 'validator',
                                 'input_type', 'input_size'])

magresVersionArguments = {
    'magresFilesID': basestring,
    'date': datetime
}

magresVersionOptionals = OrderedDict([
    ('doi', OptVArg('DOI', basestring,
                    'text',
                    '35')),
    ('notes', OptVArg('Notes', basestring,
                      'textarea',
                      None)),
    ('csd-ref', OptVArg('CSD Refcode', csd_refcode_re.match,
                        'text',
                        30)),
    ('csd-num', OptVArg('CSD Number', csd_number_re.match,
                        'text',
                        30))
])

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
                 'n': int}],
    'stochiometry': [{'species': str,
                      'n': int}],
    'Z': int,
    'molecules': [[{'species': str,
                      'n': int}]]
})
