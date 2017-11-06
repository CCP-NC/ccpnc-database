const fs = require('fs');
const mVal = require('../static/js/magres-validate.js');

function validate(fname) {

    fs.readFile(fname, function(err, data) {

        console.log('Validating ' + fname);

        if (err) {
            throw(err);
        }

        var magres = mVal.validateMagres(fname, data.toString());

        if(magres) {
            console.log('Valid');
            console.log(magres);
        }
        else {
            console.log('Not valid');
        }

    });
}

// Should be good
//validate('ethanol.magres');
validate('alanine.magres');

// Designed to fail
validate('test_magres.js');

