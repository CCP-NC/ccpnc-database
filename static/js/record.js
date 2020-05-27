// Definitions for new directives

// Directive for database records
function addRecordDirective(ngApp) {

    ngApp.directive('databaseRecord', function(loginStatus) {
        return {
            templateUrl: 'templates/database_record.html',
            scope: {
                databaseRecord: '=',
                makePage: '@'
            },
            link: function(scope, elem, attr) {

                scope._edit_popup = {};
                scope.is_page = attr['makePage'] != null;

                scope.isown = function() {
                    if (!loginStatus.get_login_status()) {
                        return false;
                    }
                    else {
                        return this.databaseRecord.orcid.path == loginStatus.get_details().orcid;
                    }
                }

                // It's important to use "var" here and keep the scope local
                // or there's some reference shenanigans...
                var record_id = scope.databaseRecord._id;
                scope.edit = function() {
                    this._edit_popup = new editPopup(this, 
                                                     this.databaseRecord.chemname,
                                                     this.databaseRecord.version_history[this._selected_index],
                                                     function(scope) {
                        
                        // Please note: "this" here is the popup, NOT the record!
                        // Refer to edit.js to actually see the object
                        // This method is encapsulated anonymously here for security
                        
                        var request_data = {'_record_id': record_id};
                        var popup = this;
        
                        loginStatus.verify_token(function() {

                            $.extend(request_data, loginStatus.get_ajax_id());

                            elem.find('#edit-popup-form').ajaxSubmit({
                                data: request_data,
                                success: function(msg, status) {

                                    // Did anything go wrong?
                                    if (status != 'success') {
                                        scope.status = 'ERROR: ' + msg;
                                        scope.status_err = true;
                                    } else {
                                        scope.$parent.$parent.refresh();
                                        scope.cancel()
                                    }

                                    popup.uploading_now = false;
                                    scope.$apply();
                                },
                                error: function(err) {
                                    popup.status = 'ERROR: ' + err.responseText;
                                    popup.status_err = true;
                                    popup.uploading_now = false;
                                    scope.$apply();
                                }
                            });

                        }, function() {
                            popup.status = 'Could not authenticate ORCID details; please log in'
                            popup.status_err = true;
                        });           
                    });
                };

                scope.filename = function() {
                    return this.databaseRecord.chemname + '_v' + (parseInt(this._selected_index)+1) + '.magres';
                }

                scope.lastdate = function() {
                    // Prettify the date
                    var sdate = this.databaseRecord.last_version.date.split(' ');
                    date = sdate[0].split('-');
                    time = sdate[1].split('.')[0]; // Discard fractions of second
                    // Reorder year, month, day
                    date = date[2] + '-' + date[1] + '-' + date[0];

                    return date + ' ' + time;
                }

                // Magres calc blocks
                scope.mcalc_blocks = [];

                for (var i = 0; i < scope.databaseRecord.version_history.length; ++i) {
                    scope.mcalc_blocks.push(JSON.parse(scope.databaseRecord.version_history[i].magres_calc));
                }
            }
        };
    });

}