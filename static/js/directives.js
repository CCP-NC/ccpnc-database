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

                scope.formData = {};

                scope.edit = function() {
                    this.formData.is_open = true;
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

                if (scope.submit == null) {
                    scope.submit = scope.cancel;
                }
            }
        };
    });

}