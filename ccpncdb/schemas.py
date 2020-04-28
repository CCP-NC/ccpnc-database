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

# Schemas
orcidSchema = Schema({
    'path': orcid_path_re.match,
    'host': str,
    'uri': orcid_path_re.search,
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
    # User input, mandatory
    'license': lictypes,
    # User input, optional
    Optional('user_institution', ''): str,
    Optional('doi', ''): str,
    Optional('extref', ''): str,
    Optional('csd_ref', ''): csd_refcode_re.match,
    Optional('csd_num', ''): csd_number_re.match,
    Optional('chemform', ''): str,
    Optional('notes', ''): str
})

magresVersionSchemaAutomatic = Schema({
    # Automatically generated
    'date': datetime,
    'magresFilesID': str
})

magresVersionSchema = _merge_schemas(magresVersionSchemaUser,
                                     magresVersionSchemaAutomatic)

magresRecordSchemaUser = Schema({
    # User input, mandatory
    'chemname': And(str, len),
    'orcid': orcidSchema,
    # User input, optional
})

magresRecordSchemaAutomatic = Schema({
    # Automatically generated
    'visible': bool,
    'mdbref': str,
    'user_name': And(str, len),
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
                    'n': int}]],
    'version_count': int,
    'version_history': [magresVersionSchema],
    Optional('last_version', None): magresVersionSchema,
})

magresRecordSchema = _merge_schemas(magresRecordSchemaUser,
                                    magresRecordSchemaAutomatic)

