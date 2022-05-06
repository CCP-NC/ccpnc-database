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
var TableProperty = function(name, short_name, value, size, type, hidden) {
    this.name = name;
    this.short_name = short_name;
    this.value = value;
    this.size = size || 35;
    this.type = type || 'text';
    this.hidden = hidden;
}

// The edit table template is retrieved from the server
var edit_table_template = [];
$.ajax({
    url: ccpnc_config.server_app + '/optionals',
    type: 'GET',
    crossDomain: true,
    dataType: 'JSON'
}).done(function(r) {
    edit_table_template = r;
});

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
    this._props = [];
    for (var i = 0; i < edit_table_template.length; ++i) {
        var opt = edit_table_template[i];
        this._props.push(new TableProperty(opt.full_name, opt.short_name,
            '', opt.input_size, opt.input_type));
    }

    if (properties == null) { // Passes any previously existing values
        properties = {};
    }

    for (var p in properties) {
        for (var i = 0; i < this._props.length; ++i) {
            var prop = this._props[i];
            if (prop.short_name == p) {
                prop.value = properties[p];
            }
        }
    }

    this.get_props = function() {
        var prop_dict = {};

        for (var i = 0; i < this._props.length; ++i) {
            var p = this._props[i];
            prop_dict[p.short_name] = p.value;
        }

        return prop_dict;
    }
}