import re
import inspect
from ccpncdb.utils import extract_stochiometry

def _formula_read(f):
    cfre = re.compile('([A-Z][a-z]*)([0-9]*)')

    if (cfre.match(f) is None):
        raise ValueError('Invalid formula string')

    match = []
    for el in cfre.findall(f):
        n = int(el[1]) if el[1] != '' else 1
        match.append({
            'species': el[0],
            'n': n
        })

    return match


def search_by_ms(sp, minms, maxms):

    return [
        {'nmrdata': {'$elemMatch': {'species': sp}}},
        {'nmrdata': {'$elemMatch':
                     {'$nor': [{'msiso': {'$lt': float(minms)}},
                               {'msiso': {'$gt': float(maxms)}}]}
                     }
         }
    ]


def search_by_doi(doi):

    return [
        {'last_version.doi': doi}
    ]


def search_by_orcid(orcid):

    return [
        {'orcid.path': orcid}
    ]


def search_by_chemname(pattern):

    regex = re.compile(pattern.replace(".", "\\.").replace(
        "*", ".*").replace("?", "."), re.IGNORECASE)
    # escape ., convert * to any character, convert ? to a single character

    return [
        {'chemname': {'$regex': regex}}
    ]


def search_by_chemform(pattern):

    regex = re.compile(pattern.replace(".", "\\.").replace(
        "*", ".*").replace("?", "."), re.IGNORECASE)
    # escape ., convert * to any character, convert ? to a single character

    return [
        {'last_version.chemform': {'$regex': regex}}
    ]


def search_by_formula(formula, subset=False):

    formula = _formula_read(formula)
    stochio = extract_stochiometry(formula)
    # Check for stochiometry
    if not subset:
        return [{
            'stochiometry': stochio
        }]
    else:
        return [{
            'stochiometry': {
                '$elemMatch': {
                    '$and': [
                        {'species': f['species']},
                        {'n': {'$gte': f['n']}}
                    ]
                }
            }
        } for f in stochio]


def search_by_molecule(formula):

    formula = _formula_read(formula)

    return [{'molecules': {
        '$in': [formula]
    }}]


def search_by_csdref(csdref):

    return [
        {'last_version.csd_ref': csdref}
    ]


def search_by_csdnum(csdnum):

    return [
        {'last_version.csd_num': csdnum}
    ]


def search_by_license(license):
    return [
        {'last_version.license': license}
    ]


def search_by_mdbref(mdbref):
    return [
        {'mdbref': mdbref}
    ]


# Function dictionary
search_functions = {name[10:]: obj for name, obj in locals().items()
                    if name[:10] == 'search_by_'}


def build_search(search_spec):

    search_dict = {
        '$and': [{'visible': True}]
    }

    # Build the string
    for src in search_spec:
        try:
            search_func = search_functions[src.get('type')]
        except KeyError:
            raise ValueError('Invalid search type')

        # Find arguments
        args = inspect.getfullargspec(search_func).args

        # Get them as dict
        try:
            args = {a: src['args'][a] for a in args}
        except KeyError:
            raise ValueError('Invalid search arguments')

        search_dict['$and'] += search_func(**args)

    return search_dict
