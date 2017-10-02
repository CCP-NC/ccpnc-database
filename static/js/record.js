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