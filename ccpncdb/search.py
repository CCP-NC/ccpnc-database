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

    # Build the overall query by checking ifthe nmrdata exists combined with the 
    # single_query for the ranged search
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
        # sbquery = {'chemname': {'$regex': regex, '$options': 'i'}}
        sbquery = {'chemname': {'$regex': regex}} #regex already includes re.IGNORECASE, setting $options to 'i' is redundant and causes an error
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


def search_by_extref(reftype, refcode, other_reftype=None): #other_reftype is only used when reftype is 'other'

    q = {}
    
    # If no database name has been selected by the user from the dropdown list in search form, 
    # the refcode carries the value ''. For MongoDB search quesy, the empty string needs to be 
    # converted to None for the query to work.
    if refcode == '':
        refcode = None
    # If user types text and deletes it from field, the entry is registered as '' rather 
    # than None. For simplicity of handling, empty values are always to be recorded as None 
    # for use by function.
    if reftype == '':
        reftype = None

    # The external database name chosen fro m the dropdown list in search form has to be searched 
    # as an exact match. Partial search strings are permissible for the freetext search when refcode = 'other'.
    if reftype is not None:
        if reftype == 'other':
            #ignore doing the exact match search for user entered database names in free text
            if other_reftype is not None: #user enters database name as free text
                reftype_other = re.compile(other_reftype, re.IGNORECASE)
                q['$or'] = [{'$and': [{'last_version.extref_type': 'other'},
                                      {'last_version.extref_other': {'$regex': reftype_other}}]}]
            else: #user does not enter database name as free text
                reftype_other = "None"
                q['$or'] = [{'$and': [{'last_version.extref_type': 'other'},
                                      {'last_version.extref_other': {'$regex': reftype_other, '$options': 'i'}}]}]
        else:
            #ignore the other category in extref_type if user has chosen a database name from the dropdown list
            reftype_exact = re.compile(rf"^{reftype}$",re.IGNORECASE)
            reftype_other = None

        if reftype_exact:
            q['$or'] = [{'last_version.extref_type': {'$regex': reftype_exact}}]

        #legacy code
        # q['$or'] = [
        #     {'last_version.extref_type': {'$regex': reftype_exact}},
        #     {'$and': [{'last_version.extref_type': 'other'},
        #               {'last_version.extref_other':
        #                {'$regex': reftype_other}}]}
        # ]
        
    # The external database reference code can be searched as an exactly matched or partially matched string. 
    # This code block accommodates wildcard searches with * indicating any number of characters and ? indicating 
    # a single character.
    if refcode is not None:
        if '*' in refcode or '?' in refcode:
            # Replace '*' with '.*' to match any number of characters
            # Replace '?' with '.' to match any single character
            regex_pattern = re.compile(rf"^{refcode.replace('*', '.*').replace('?', '.')}$", re.IGNORECASE)
            q['last_version.extref_code'] = {'$regex': regex_pattern}
        else: #absence of wildards in freetext uses the search string for an exact string match search
            #replaced original code to treat search string as an exact match
            regex_pattern = '^' + refcode + '$'
            q['last_version.extref_code'] = {'$regex': regex_pattern, '$options': 'i'}
        #legacy code    
        # q['last_version.extref_code'] = {'$regex': refcode, '$options': 'i'}

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
        
        #Extract boolean choice to determine how to manipulate the query returned by search functions
        bool_inspect = src.get('boolean')
        
        # Get them as dict
        try:
            args = {a: src['args'][a] for a in args}
        except KeyError:
            raise ValueError('Invalid search arguments')

        # Receive query in a buffer variable first
        query_buffer = search_func(**args)
        query_add=[]
        # Make choice to pass query as such or negate it based on user's Boolean filtering choice in 'boolean' key
        if not bool_inspect: #AND - pass query as is
            print('Am here!')
            if src.get('type') == 'extref': #catch code to ensure database name and reference code are non-empty in returned records
                query_add=[{'$and':[query_buffer[0],{'last_version.extref_type':{'$ne': None}},{'last_version.extref_code':{'$ne': None}}]}]
            else: # search parameters other than extref
                query_add=query_buffer
        elif bool_inspect: #NOT - negate search query
            if src.get('type') == 'extref': #catch code to ensure database name and reference code are non-empty in returned records even when negating
                query_add=[{'$and':[{'$nor':query_buffer},{'last_version.extref_type':{'$ne': None}},{'last_version.extref_code':{'$ne': None}}]}]
            else: # search parameters other than extref
                query_add=[{'$nor':query_buffer}]
        # Retain old code for search_dict as backup
        # search_dict['$and'] += search_func(**args)
        # Add query to search_dict after applying changes as necessary
        search_dict['$and'] += query_add

    return search_dict
