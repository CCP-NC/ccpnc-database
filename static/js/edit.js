// Directive for edit form
function addEditFormDirective(ngApp) {

    ngApp.directive('editForm', function() {
        return {
            templateUrl: 'templates/edit_form.html',
            scope: {
                editForm: '=',
            },
            // Associated functions
            link: function(scope, elem, attr) {

                scope.cancel = function() {
                    this.editForm.is_open = false;
                };

                scope.submit = function() {
                    if (this.editForm.submit != null)
                        this.editForm.submit();
                    this.editForm.is_open = false;
                }
            }
        };
    });
}

// Object creator for edit form scope
// Takes: reference to the parent scope, object with editable properties, 
// submit callback
var editFormScope = function(parent, properties, submit) {
    this.is_open = true;
    this.parent = this;
    this.submit = submit;

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