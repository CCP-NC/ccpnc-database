var validateMagres = function(fname, ftxt) {
    // Validate a .magres file

    // First check the extension, of course
    var spl = fname.split('.');
    var ext = spl[spl.length-1];

    if (ext != 'magres') {
        return false;
    }

    // Now the first line
    var header = '#$magres-abinitio';
    var fline = ftxt.split('\n')[0];
    if (fline.indexOf(header) < 0) {
        return false;
    }

    return true;
}