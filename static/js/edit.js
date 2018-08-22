// Directive for edit form
function addEditPopupDirective(ngApp) {

    ngApp.directive('editPopup', function() {
        return {
            templateUrl: 'templates/edit_popup.html',
            scope: {
                editPopup: '=',
            },
            // Associated functions
            link: function(scope, elem, attr) {

                scope.cancel = function() {
                    this.editPopup.is_open = false;
                };

                scope.submit = function() {
                    if (this.editPopup.submit != null)
                        this.editPopup.submit(scope);

                    if (this.editPopup.close_onsub)
                        this.cancel();
                }

                scope.load_files = function(files) {

                    var popup = this.editPopup;

                    // Must be only one file for now
                    if (files.length != 1) {
                        popup.status = 'Only one file can be uploaded at a time';
                        popup.status_err = true;
                        return;
                    } else {
                        var file = files[0];
                        popup.status = '';
                        popup.status_err = false;

                        var reader = new FileReader();
                        reader.onload = (function(fevent) {
                            var mtext = fevent.currentTarget.result;
                            popup.uploading_now = false;
                            if (validateMagres(file.name, mtext)) {
                                popup.magres_file_name = file.name;
                                popup.magres_file = mtext;
                                popup.status_err = false;
                                popup.status = 'File ready to upload';
                            } else {
                                popup.magres_file_name = '';
                                popup.magres_file = null;
                                popup.status_err = true;
                                popup.status = 'The file is not in the Magres format';
                            }
                            scope.$apply();
                        });

                        popup.uploading_now = true;
                        reader.readAsText(file);
                    }
                }
            }
        };
    });
}

function addEditTableDirective(ngApp) {

    ngApp.directive('editTable', function() {
        return {
            templateUrl: 'templates/edit_table.html',
            scope: {
                editTable: '=',
            },
        }
    })

}

// Table property
var TableProperty = function(name, value, size, is_area, hidden) {
    this.name = name;
    this.value = value;
    this.size = size || 35;
    this.is_area = is_area;
    this.hidden = hidden;
}

// Object creator for edit form scope
// Takes: reference to the parent scope, object with editable properties, 
// submit callback
var editPopup = function(parent, name, properties, submit, close_onsub) {
    this.is_open = true;
    this.parent = parent;
    this.name = name;
    this.submit = submit;
    this.close_onsub = close_onsub;

    this.status = '';
    this.status_err = false;
    this.magres_file_name = '';
    this.magres_file = null;
    this.uploading_now = false;

    this._table = new editTable(this, properties);
}

var editTable = function(parent, properties) {
    this.parent = parent;

    // Gather all the editable properties
    this._props = {
        'doi': new TableProperty('DOI', ''),
        'author': new TableProperty('Author(s)', '', 100),
    };

    if (properties == null) { // Passes any previously existing values
        properties = {};
    }

    for (var p in this._props) {
        this._props[p].value = properties[p] || this._props[p].value;
    }

    this.get_props = function() {
        var prop_dict = {};

        for (var p in this._props) {
            prop_dict[p] = this._props[p].value;
        }

        return prop_dict;
    }
}