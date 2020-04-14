import re
from datetime import datetime
from collections import namedtuple, OrderedDict
from schema import Schema, And, Optional


def _one_of(vals):
    # Convenient tool for multiple values validation
    def f(d):
        return (d in vals)
    return f


def _merge_schemas(s1, s2):
    d = dict(s1.schema)
    d.update(s2.schema)
    return Schema(d)


"""Data schemas for entries to be uploaded to the Database."""

orcid_path_re = re.compile('[0-9]{4}-'*3+r'[0-9]{3}[0-9X]{1}\Z')
csd_refcode_re = re.compile(r'[A-Z]{6}([0-9]{2})?\Z')
csd_number_re = re.compile(r'[0-9]{6,7}\Z')

# License types
lictypes = _one_of(['pddl', 'odc-by', 'cc-by'])

# Optional arguments for each magres version. These are useful also
# client-side so we store them in their own definitions

OptVArg = namedtuple('OptVArg', ['full_name', 'validator',
                                 'input_type', 'input_size'])

magresVersionArguments = {
    'magresFilesID': str,
    'date': datetime
}

magresVersionOptionals = OrderedDict([
    ('doi', OptVArg('DOI', str,
                    'text',
                    '35')),
    ('notes', OptVArg('Notes', str,
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
    'host': str,
    'uri': orcid_path_re.search,
})

magresVersionSchema = Schema(magresVersionArguments)

magresMetadataSchema = Schema({
    'chemname': And(str, len),
    'chemform': str,
    'license': lictypes,
    'orcid': orcidSchema,
    'version_history': [magresVersionSchema]
})

magresIndexSchema = Schema({
    'chemname': And(str, len),
    'chemform': str,
    'license': lictypes,
    'orcid': orcidSchema,
    'metadataID': str,
    'latest_version': magresVersionSchema,
    'values': [{
        'species': str,
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

# Two types of elements:
#   - Records
#   - Versions (multiple for each record)
#
# For each of them there's three types of possible arguments:
#   - User input, mandatory
#   - User input, optional
#   - Automatically generated

magresVersionSchemaUser = Schema({
})

magresVersionSchemaAutomatic = Schema({
    'date': datetime,
    'magresFilesID': str
})

magresVersionSchema = _merge_schemas(magresVersionSchemaUser,
                                     magresVersionSchemaAutomatic)

magresRecordSchemaUser = Schema({
    # User input, mandatory
    'chemname': And(str, len),
    'orcid': orcidSchema,
    'license': lictypes,
    'user_name': And(str, len),
    'user_institution': And(str, len),
    'doi': And(str, len),
    # User input, optional
    Optional('csd_ref', ''): csd_refcode_re.match,
    Optional('csd_num', ''): csd_number_re.match,
    Optional('chemform', ''): str
})

magresRecordSchemaAutomatic = Schema({
    # Automatically generated
    'mdbref': str,
    'version_history': [magresVersionSchema],
    'nmrdata': [{
        'species': str,
        'msiso': [float],
    }],
    'formula': [{'species': str,
                 'n': int}],
    'stochiometry': [{'species': str,
                      'n': int}],
    'Z': int,
    'molecules': [[{'species': str,
                    'n': int}]]
})

magresRecordSchema = _merge_schemas(magresRecordSchemaUser,
                                    magresRecordSchemaAutomatic)
