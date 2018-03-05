// Definitions for new directives

// Directive for database records
function addRecordDirective(ngApp) {

    ngApp.directive('databaseRecord', function() {
        return {
            templateUrl: 'templates/database_record.html',
            scope: {
                databaseRecord: '=',
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
            }
        };
    });

}