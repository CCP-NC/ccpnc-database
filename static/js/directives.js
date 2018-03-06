// Definitions for new directives

// Directive for database records
function addRecordDirective(ngApp) {

    ngApp.directive('databaseRecord', function() {
        return {
            templateUrl: 'templates/database_record.html',
            scope: {
                databaseRecord: '=',
            },
            link: function(scope, elem, attr) {

                scope._edit_form = {};

                scope.edit = function() {
                    this._edit_form.is_open = true; 
                    this._edit_form.parent = this;

                    // Gather all the editable properties
                    var editable_props = ['doi'];
                    this._edit_form._props = {};

                    for (var i = 0; i < editable_props.length; ++i) {
                        var p = editable_props[i];
                        this._edit_form._props[p] = this.databaseRecord.version_history[this._selected_index][p];
                    }

                    this._edit_form.submit = function() {
                        console.log(this._props);
                    }
                };           
            }
        };
    });

}

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