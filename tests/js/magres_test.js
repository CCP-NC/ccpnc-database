const assert = require('assert');
const fs = require('fs');
const mVal = require('../../static/js/magres-validate.js');

const mfiles = ['../data/ethanol.magres', '../data/alanine.magres']


function load(fname) {
    data = fs.readFileSync(fname);
    return mVal.validateMagres(fname, data.toString());
}

describe('magres-validate.js', function () {
  describe('#validateMagres()', function () {

    it('should return data for valid magres files', function () {
        for (var i = 0; i < mfiles.length; ++i) {
            var fname = mfiles[i];
            var magres = load(fname);
            assert.ok(magres);
        }
    });

    it('should return false for invalid magres files', function () {
        var fname = 'magres_test.js';
        var magres = load(fname);
        assert.equal(magres, false);
    });

  });
});
