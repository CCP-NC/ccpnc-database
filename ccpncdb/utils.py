import re
import numpy as np
from io import StringIO
from ase.io.magres import read_magres
from soprano.properties.linkage import Molecules
from soprano.properties.nmr.ms import MSIsotropy
from soprano.properties.nmr.efg import EFGVzz
from soprano.nmr import NMRTensor
from soprano.nmr.utils import _haeb_sort


def prime_factors(num):
    # Prime factors of num
    n = 2
    facs = []
    while num > 1:
        while num % n == 0:
            facs.append(n)
            num = num/n
        n += 1 + (n > 2)  # So past 2 test only odd numbers

    return sorted(facs)


def get_name_from_orcid(user_info):
    # Retrieve a user name from an ORCID record

    # Is there a credit name?
    if user_info['person']['name']['credit-name'] is not None:
        name = user_info['person']['name']['credit-name']['value']
    else:
        try:
            name = user_info['person']['name']['given-names']['value']
            name += ' ' + user_info['person']['name']['family-name']['value']
        except KeyError:
            # I got nothing
            return None

    return name


def get_schema_keys(schema):
    # Extract a list of keys from a given schema
    raw_keys = schema.schema.keys()
    keys = []
    for k in raw_keys:
        if hasattr(k, 'schema'):
            keys.append(k.schema)
        else:
            keys.append(k)

    return sorted(keys)


def set_null_values(data, schema, pattern=''):
    keys = get_schema_keys(schema)

    # Set as None all values that match pattern
    for k in keys:
        if k not in data or data[k] == pattern:
            data[k] = None

    return data


def split_data(data, s1, s2):
    # Split data between two schemas
    sd1, sd2 = {}, {}
    sk1 = get_schema_keys(s1)
    sk2 = get_schema_keys(s2)
    for k, v in data.items():
        if k in sk1:
            sd1[k] = v
        elif k in sk2:
            sd2[k] = v

    return sd1, sd2


def tokenize_name(name):
    # Split a chemname, extract useful keywords from it
    sep = re.compile('[0-9,\\\'\\(\\)\\[\\]\\s\\-]+')
    tokens = sep.split(name)
    tokens = [tk.lower() for tk in tokens if len(tk) > 1]
    return tokens

def read_magres_file(mfile):
    # Read a magres file/string unifying the output into an ASE Atoms object
    if hasattr(mfile, 'read'):
        mstr = mfile.read()
    else:
        mstr = mfile

    if hasattr(mstr, 'decode'):
        mstr = mstr.decode('utf-8')
    matoms = read_magres(StringIO(mstr))

    return {'string': mstr, 'Atoms': matoms}


def extract_formula(magres=None, symbols=None):
    # Return a list describing the compound's formula
    if symbols is None:
        symbols = magres.get_chemical_symbols()
    else:
        symbols = list(symbols)
    formula = [{'species': s, 'n': symbols.count(s)} for s in set(symbols)]
    formula = sorted(formula, key=lambda x: x['species'])

    return formula


def extract_stochiometry(formula):
    # Stochiometry from formula

    counts = [prime_factors(x['n']) for x in formula]

    c = 1
    while all([len(x) > 0 for x in counts]):
        ff = [x.pop(0) for x in counts]
        if len(set(ff)) == 1:
            c *= ff[0]
        else:
            break

    stochio = []
    for x in formula:
        sx = {}
        sx.update(x)
        sx['n'] = int(sx['n']/c)
        stochio.append(sx)

    return stochio


def extract_molecules(magres):

    mols = Molecules.get(magres)
    syms = np.array(magres.get_chemical_symbols())

    mols_f = [extract_formula(symbols=syms[m.indices]) for m in mols]

    return mols_f


def extract_elements(formula):
    return list([f['species'] for f in formula])


def extract_elements_ratios(formula):
    ratios = np.array([float(f['n']) for f in formula])
    ratios /= np.sum(ratios)

    return list(ratios)


def extract_tensdata(tensor):
    evals = tensor.eigenvalues
    haeb_evals = _haeb_sort([evals])[0]

    return {'e_x': haeb_evals[0], 'e_y': haeb_evals[1], 'e_z': haeb_evals[2]}


def extract_nmrdata(magres):

    # Chemical species
    symbols = np.array(magres.get_chemical_symbols())
    sp = {s: np.where(symbols == s) for s in set(symbols)}

    species = sorted(sp.keys())
    nmrdata = [{'species': s} for s in species]

    # Try adding individual nmr data
    if magres.has('ms'):
        ms = magres.get_array('ms')
        ms = np.array([NMRTensor(T) for T in ms])
        for i, s in enumerate(species):
            inds = sp[s]
            nmrdata[i]['ms'] = [extract_tensdata(T) for T in ms[inds]]

    if magres.has('efg'):
        efg = magres.get_array('efg')
        efg = np.array([NMRTensor(T) for T in efg])
        for i, s in enumerate(species):
            inds = sp[s]
            nmrdata[i]['efg'] = [extract_tensdata(T) for T in efg[inds]]

    return nmrdata
