const fs = require('fs');
const mVal = require('../../static/js/magres-validate.js');

function validate(fname) {

    data = fs.readFileSync(fname);

    var magres = mVal.validateMagres(fname, data.toString());

    if(magres) {
        return true;
    }
    else {
        return false;
    }
}

tests = [
    [validate('../data/ethanol.magres'), true], 
    [validate('../data/alanine.magres'), true],
    [validate('test_magres.js'), false]
];

for (var i = 0; i < tests.length; ++i) {
    console.log('Test ' + (i+1) + ':');
    var res = tests[i][0];
    if (res == tests[i][1]) {
        console.log('Passed');
    }
    else {
        console.log('Failed');
    }
}
