import re
from datetime import datetime
from collections import namedtuple, OrderedDict
from schema import Schema, And, Optional, Or
from schema import (SchemaError, SchemaMissingKeyError)


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
namestr_re = re.compile(r'[\x00-\x7F]*\Z')

# License types
lictypes = _one_of(['pddl', 'odc-by', 'cc-by'])

# Schemas
orcidSchema = Schema({
    'path': orcid_path_re.match,
    'host': str,
    'uri': orcid_path_re.search,
})

tensorSchema = Schema({
    'e_x': float,
    'e_y': float,
    'e_z': float
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
    Optional('doi', None): Or(str, None),
    Optional('chemform', None): Or(namestr_re.match, None),
    Optional('notes', None): Or(namestr_re.match, None),
    Optional('extref_type', None): Or(namestr_re.match, None),
    Optional('extref_other', None): Or(namestr_re.match, None),
    Optional('extref_code', None): Or(namestr_re.match, None)
})

magresVersionSchemaAutomatic = Schema({
    # Automatically generated
    'date': datetime,
    'magresFilesID': str,
    'magres_calc': Or(str, None),
})

magresVersionSchema = _merge_schemas(magresVersionSchemaUser,
                                     magresVersionSchemaAutomatic)

magresRecordSchemaUser = Schema({
    # User input, mandatory
    'chemname': And(namestr_re.match, len),
    'orcid': orcidSchema,
    # User input, optional
    Optional('user_name'): And(str, len)
})

magresRecordSchemaAutomatic = Schema({
    # Automatically generated
    'id': str,
    'type': str,
    'immutable_id': str,
    'last_modified': datetime,
    'chemname_tokens': [str],
    'elements': [str],
    'nelements': int,
    'elements_ratios': [float],
    'chemical_formula_descriptive': str,
    'visible': bool,
    'nmrdata': [{
        'species': str,
        Optional('ms'): [tensorSchema],
        Optional('efg'): [tensorSchema],
        Optional('msiso'): [float],
        Optional('efgvzz'): [float]
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
    'last_version': Or(magresVersionSchema, None)
})

magresRecordSchema = _merge_schemas(magresRecordSchemaUser,
                                    magresRecordSchemaAutomatic)

# Keys to actually list in the standard CSV file for archives
csvProperties = ['chemname', 'license', 'doi', 'chemform',
                 'extref_type', 'extref_other', 'extref_code', 
                 'notes']

ValidationResult = namedtuple('ValidationResult',
                              ['result', 'missing', 'invalid'])


def validate_with(data, schema):

    # Validate the data with the given schema, but return extracted info
    # on what has gone wrong (if anything)

    result = True
    missing = []
    invalid = None

    try:
        schema.validate(data)
    except SchemaMissingKeyError as e:
        # Parse which ones are missing
        kw = str(e).split(':')[1].split(',')
        kw = list(map(lambda s: s.strip()[1:-1], kw))
        missing = kw
        result = False
    except SchemaError as e:
        result = False
        invalid = re.compile('ey \'([a-zA-Z0-9_]+)\''
                             ).findall(str(e))[0]

    return ValidationResult(result, missing, invalid)
