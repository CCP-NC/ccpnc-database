import re
from ase.io.magres import read_magres
from schema import Schema, And, Optional

"""A schema for entries to be uploaded to the Database.
This currently does not include the cross-referencing IDs, as they are 
obligatory but enforced by the uploading process itself."""

orcid_path_re = re.compile('[0-9]{4}-'*3+'[0-9]{3}[0-9X]{1}\Z')

magresDataSchema = Schema({
    'chemname': And(str, len),
    'orcid': {
        'path': orcid_path_re.match,
        'host': str,
        'uri': orcid_path_re.search,
    },
    Optional('doi'): str,
    Optional('notes'): str,
    Optional('metadata'): dict
})

magresFileSchema = Schema({
    'magres': And(str, len)
})
