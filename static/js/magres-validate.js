var validateMagres = function(fname, ftxt) {
    // Validate a .magres file

    // First check the extension, of course
    var spl = fname.split('.');
    var ext = spl[spl.length-1];

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
            }
            else {
                curr_block = match_b[2];
                blocks[curr_block] = [];
            }
        }
        else if (curr_block != null) {
            blocks[curr_block].push(flines[i]);
        }
    }
    if (curr_block != null || !('atoms' in blocks) || !('magres' in blocks)) {
        // Invalid or corrupted file
        return false;
    }

    return data;
}

// For testing with Node.js
module.exports.validateMagres = validateMagres;