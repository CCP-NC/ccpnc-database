import re
import inspect
from ccpncdb.utils import extract_stochiometry, tokenize_name


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

# Expressions for NMR quantities in aggregation queries


def _expr_vzz(name):
    return '$${0}.e_z'.format(name)


def _expr_iso(name):
    return {'$avg': ['$${0}.e_x'.format(name),
                     '$${0}.e_y'.format(name),
                     '$${0}.e_z'.format(name)]}


def _expr_nmrrange(sp, var, expr, minv, maxv):

    minv = float(minv)
    maxv = float(maxv)

    single_query = {'$and': [
        {'$eq': ['$$nmrd.species', sp]},
        {'$anyElementTrue': {
            '$map': {
                'input': '$$nmrd.{0}'.format(var),
                'as': '{0}'.format(var),
                'in': {
                    '$and': [
                            {'$gte': [expr(var), minv]},
                            {'$lte': [expr(var), maxv]}
                    ]
                }
            }
        }
        }
    ]}

    all_query = [{'$and':[
        {'nmrdata.{0}'.format(var): {'$exists': True}},
        {'$expr': {'$anyElementTrue': {
            '$map': {
                'input': '$nmrdata',
                'as': 'nmrd',
                'in': single_query
            }
        }
        }
        },]}
    ]

    return all_query


def search_by_msRange(sp, minms, maxms):

    return _expr_nmrrange(sp, 'ms', _expr_iso, minms, maxms)


def search_by_efgRange(sp, minefg, maxefg):

    return _expr_nmrrange(sp, 'efg', _expr_vzz, minefg, maxefg)


def search_by_doi(doi):
    # Return no result if the user has left the search field 
    # blank
    if doi is None or doi == '':
        return []
    
    # If a wildcard is detected in user entered search text, 
    # escape the wildcard to perform a partial string search. 
    # If no wildcard is detected, exact string match is 
    # performed to search. Partial search string with no 
    # wildcard will return 0 results.
    if "*" in doi:
        doi = doi.replace("*", ".*")
    else:
        doi = doi.replace(".","\\.")
        doi = '^'+doi+'$'
    return [
        {'last_version.doi':
            {'$regex': doi, '$options': 'i'}
            }
        ]

    #Legacy code backup
    # doi = re.escape(doi)
    # doi = doi.replace(".", "\\.").replace(
    #     "*", ".*").replace("?", ".")
    #regex = re.compile('.*{0}.*'.format(doi))


def search_by_orcid(orcid):

    return [
        {'orcid.path': orcid}
    ]


def search_by_chemname(pattern):

    if pattern is None or pattern == '':
        return []

    # Start by splitting the pattern in bits in quotes and bits outside them
    quotere = re.compile('"([^\"]+)"')
    substrings = quotere.findall(pattern)

    query = {
        '$or': [
        ]
    }

    # Start by finding the substrings in chemname
    if len(substrings) > 0:
        query['$or'].append({'$and': []})
    for sb in substrings:
        # regex = re.compile(sb.replace(".", "\\.").replace(
        # "*", ".*").replace("?", "."), re.IGNORECASE)
        regex = re.compile(sb.replace("*", ".*"), re.IGNORECASE)
        sbquery = {'chemname': {'$regex': regex, '$options': 'i'}}
        query['$or'][0]['$and'].append(sbquery)
        pattern = pattern.replace('"{0}"'.format(sb), '')

    # Now tokens
    tokens = tokenize_name(pattern)

    if len(tokens) > 0:
        query['$or'].append({'$and': []})
    for tk in tokens:
        query['$or'][-1]['$and'].append({'chemname_tokens': tk})

    return [query]


def search_by_chemform(pattern):

    # regex = re.compile(pattern.replace(".", "\\.").replace(
    #     "*", ".*").replace("?", "."), re.IGNORECASE)
    regex = pattern.replace(".", "\\.").replace(
        "*", ".*").replace("?", ".")
    # escape ., convert * to any character, convert ? to a single character

    return [
        {'last_version.chemform': {'$regex': regex, '$options': 'i'}}
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


def search_by_extref(reftype, refcode):

    q = {}

    if reftype is not None:
        q['$or'] = [
            {'last_version.extref_type': {'$regex': reftype, '$options': 'i'}},
            {'$and': [{'last_version.extref_type': 'other'},
                      {'last_version.extref_other':
                       {'$regex': reftype, '$options': 'i'}}]}
        ]
    if refcode is not None:
        q['last_version.extref_code'] = {'$regex': refcode, '$options': 'i'}

    return [q]


def search_by_license(license):
    return [
        {'last_version.license': license}
    ]


def search_by_mdbref(mdbref):
    return [
        {'immutable_id': mdbref}
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
        
        #Extract boolean choice for function
        bool_inspect = src.get('boolean')
        
        # Get them as dict
        try:
            args = {a: src['args'][a] for a in args}
        except KeyError:
            raise ValueError('Invalid search arguments')

        # Receive query in a buffer variable first
        query_buffer = search_func(**args)
        query_add=[]
        # Make choice to pass query as such or negate it based on user's Boolean filtering choice
        if bool_inspect == '10':
            query_add=query_buffer
        elif bool_inspect == '01':
            query_add=[{'$nor':query_buffer}]
        # Retain old code for search_dict as backup
        # search_dict['$and'] += search_func(**args)
        # Add query to search_dict after applying changes as necessary
        search_dict['$and'] += query_add

    return search_dict
