// Definitions for new directives

// Directive for database records
function addRecordDirective(ngApp) {

    ngApp.directive('databaseRecord', function(loginStatus) {
        return {
            templateUrl: 'templates/database_record.html',
            scope: {
                databaseRecord: '=',
            },
            link: function(scope, elem, attr) {

                scope._edit_popup = {};

                // It's important to use "var" here and keep the scope local
                // or there's some reference shenanigans...
                var index_id = scope.databaseRecord.index_id;

                scope.isown = function() {
                    if (!loginStatus.get_login_status()) {
                        return false;
                    }
                    else {
                        return this.databaseRecord.orcid == loginStatus.get_details().orcid;
                    }
                }

                scope.edit = function() {
                    this._edit_popup = new editPopup(this, 
                                                    this.databaseRecord.chemname,
                                                    this.databaseRecord.version_history[this._selected_index],
                                                    function(scope) {
                        
                        // Please note: "this" here is the popup, NOT the record!
                        // Refer to edit.js to actually see the object
                        // This method is encapsulated anonymously here for security

                        request_data = $.extend({
                            index_id: index_id, 
                        }, this._table._props);                        
                        if (this.magres_file_name != '')
                            request_data['magres'] = this.magres_file;

                        popup = this;

                        loginStatus.verify_token(function() {
                            // Package all the data
                            details = loginStatus.get_details()
                            request_data.access_token = details['access_token'];
                            request_data.orcid = details['orcid'];

                            // Send an Ajax request
                            popup.uploading_now = true;

                            $.ajax({
                                url: ngApp.server_app + '/edit',
                                type: 'POST',
                                crossDomain: true,
                                data: request_data
                            }).done(function(r) {
                                // Did anything go wrong?
                                if (r != 'Success') {                        
                                    popup.status = 'ERROR: ' + r;
                                    popup.status_err = true;
                                }
                                else {
                                    // Refresh and close
                                    scope.$parent.$parent.refresh();
                                    scope.cancel();
                                }

                                popup.uploading_now = false;
                                scope.$apply();

                            }).fail(function(e) {
                                popup.status = 'ERROR: ' + e.responseText;
                                popup.status_err = true;
                                popup.uploading_now = false;
                                scope.$apply();
                            });

                        }, function() {
                            popup.status = 'Could not authenticate ORCID details; please log in'
                            popup.status_err = true;
                            console.log(popup.status);
                        });                        
                    });
                };

                scope.filename = function() {
                    return this.databaseRecord.chemname + '_v' + (parseInt(this._selected_index)+1) + '.magres';
                }
            }
        };
    });

}