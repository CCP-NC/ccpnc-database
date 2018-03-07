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

                scope._edit_popup = {};

                scope.edit = function() {
                    this._edit_popup = new editPopup(this, 
                                                    this.databaseRecord.chemname,
                                                    this.databaseRecord.version_history[this._selected_index],
                                                    function() {
                        console.log(this._table._props);
                        console.log(this.magres_file_name);
                    });
                };
            }
        };
    });

}