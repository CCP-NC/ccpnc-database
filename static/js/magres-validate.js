var validateMagres = function(fname, ftxt) {
    // Validate a .magres file

    // First check the extension, of course
    var spl = fname.split('.');
    var ext = spl[spl.length - 1];

    if (ext != 'magres') {
        return false;
    }

    data = {};

    var flines = ftxt.split('\n');

    // Now the first line; parse version
    var header_re = /#\$magres-abinitio-v([0-9.]+)/;
    match_v = header_re.exec(flines[0]);
    if (match_v === null) {
        return false;
    }
    data.version = match_v[1];

    // Now parse atomic formula and positions
    var block_re = /\[([\/]*)(atoms|magres)\]/;
    var curr_block = null;
    var blocks = {};

    for (var i = 1; i < flines.length; ++i) {
        match_b = block_re.exec(flines[i]);
        if (match_b != null) {
            if (match_b[1] == '/') {
                curr_block = null;
            } else {
                curr_block = match_b[2];
                blocks[curr_block] = [];
            }
        } else if (curr_block != null) {
            blocks[curr_block].push(flines[i]);
        }
    }
    if (curr_block != null || !('atoms' in blocks) || !('magres' in blocks)) {
        // Invalid or corrupted file
        return false;
    }

    // Accepted units
    var all_units = {
        'lattice': {
            'angstrom': 1,
        },
        'atom': {
            'angstrom': 1,
        },
        'ms': {
            'ppm': 1,
        }
    }

    // Parse atoms block
    var units = {}
    var cell = [];
    var atoms = [];
    var atoms_refs = {};
    var units_re = /units\s+([A-Za-z]+)\s+([A-Za-z]+)/;
    var ucell_re = /lattice\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)/;
    var atoms_re = /atom\s+([A-Za-z]{1,2})\s+([A-Za-z_0-9]+)\s+([0-9]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)/;

    for (var i = 0; i < blocks.atoms.length; ++i) {

        match_u = units_re.exec(blocks.atoms[i]);
        if (match_u) {
            units[match_u[1]] = match_u[2].toLowerCase();
            continue;
        }

        match_l = ucell_re.exec(blocks.atoms[i]);
        if (match_l != null && 'lattice' in units) {
            cell = match_l.slice(1).map(function(x) {
                return parseFloat(x) * all_units.lattice[units.lattice];
            });
        }

        match_a = atoms_re.exec(blocks.atoms[i]);
        if (match_a != null && 'atom' in units) {
            elem = match_a[1];
            label = match_a[2];
            l_i = parseInt(match_a[3]);
            xyz = match_a.slice(4).map(function(x) {
                return parseFloat(x) * all_units.atom[units.atom];
            });

            if (isNaN(l_i) || xyz.reduce(function(t, x) {
                    return isNaN(x) || t;
                }, false)) {
                // Invalid!
                return false;
            }

            if (!(label in atoms_refs)) {
                atoms_refs[label] = {};
            }

            atoms.push({
                'label': label,
                'i': l_i,
                'elem': elem,
                'xyz': xyz
            });
            atoms_refs[label][l_i] = atoms.length - 1;

            continue;
        }
    }

    data.cell = [0, 1, 2].map(function(x) {
        return cell.slice(3 * x, 3 * x + 3);
    });

    var ms_re = /ms\s+([A-Za-z_0-9]+)\s+([0-9]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)/;

    // Now parse the shieldings
    for (var i = 0; i < blocks.magres.length; ++i) {

        match_u = units_re.exec(blocks.magres[i]);
        if (match_u) {
            units[match_u[1]] = match_u[2].toLowerCase();
            continue;
        }

        match_ms = ms_re.exec(blocks.magres[i]);
        if (match_ms != null && 'ms' in units) {
            label = match_ms[1];
            l_i = parseInt(match_ms[2]);

            ms = match_ms.slice(3).map(function(x) {
                return parseFloat(x) * all_units.ms[units.ms];
            });

            if (isNaN(l_i) || ms.reduce(function(t, x) {
                    return isNaN(x) || t;
                }, false)) {
                // Invalid!
                return false;
            }

            atoms[atoms_refs[label][l_i]].ms = [0, 1, 2].map(function(x) {
                return ms.slice(3 * x, 3 * x + 3);
            });

            continue;
        }
    }

    data.atoms = atoms;

    return data;
}

// For testing with Node.js
try {
    module.exports.validateMagres = validateMagres;    
}
catch(e) {
    // Do nothing
}
