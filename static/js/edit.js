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
                        this.editPopup.submit();
                    this.editPopup.is_open = false;
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

// Object creator for edit form scope
// Takes: reference to the parent scope, object with editable properties, 
// submit callback
var editPopup = function(parent, name, properties, submit) {
    this.is_open = true;
    this.parent = this;
    this.name = name;
    this.submit = submit;

    this._table = new editTable(this, properties);
}

var editTable = function(parent, properties) {
    this.parent = parent;

    // Gather all the editable properties
    this._props = {
        'doi': '',
    };

    if (properties == null) {
        properties = {};
    }

    for (var p in this._props) {
        this._props[p] = properties[p] || this._props[p];
    }
}