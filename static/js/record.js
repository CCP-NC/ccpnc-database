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
                        return this.databaseRecord.orcid == loginStatus.get_details().orcid;
                    }
                }

                // It's important to use "var" here and keep the scope local
                // or there's some reference shenanigans...
                // var index_id = scope.databaseRecord.index_id;
                // scope.edit = function() {
                //     this._edit_popup = new editPopup(this, 
                //                                     this.databaseRecord.chemname,
                //                                     this.databaseRecord.version_history[this._selected_index],
                //                                     function(scope) {
                        
                //         // Please note: "this" here is the popup, NOT the record!
                //         // Refer to edit.js to actually see the object
                //         // This method is encapsulated anonymously here for security

                //         request_data = $.extend({
                //             index_id: index_id, 
                //         }, this._table.get_props());                        
                //         if (this.magres_file_name != '')
                //             request_data['magres'] = this.magres_file;

                //         var request_data = {
                //             index_id: index_id, 
                //         }
                //         popup = this;

                //         loginStatus.verify_token(function() {
                //             // Package all the data
                //             details = loginStatus.get_details()
                //             request_data.access_token = details['access_token'];
                //             request_data.orcid = details['orcid'];

                //             // Send an Ajax request
                //             popup.uploading_now = true;
                //             scope.$apply();

                //             $('#edit-popup-form').ajaxSubmit({
                //                 data: request_data,
                //                 success: function(r) {
                //                     // Did anything go wrong?
                //                     if (r != 'Success') {
                //                         scope.status = 'ERROR: ' + r;
                //                         scope.status_err = true;
                //                     } else {
                //                         scope.$parent.$parent.refresh();
                //                         scope.cancel()
                //                     }

                //                     popup.uploading_now = false;
                //                     scope.$apply();

                //                 },
                //                 error: function(e) {
                //                     popup.status = 'ERROR: ' + e.responseText;
                //                     popup.status_err = true;
                //                     popup.uploading_now = false;
                //                     scope.$apply();
                //                 }
                //             });                            

                //         }, function() {
                //             popup.status = 'Could not authenticate ORCID details; please log in'
                //             popup.status_err = true;
                //             console.log(popup.status);
                //         });                        
                //     });
                // };

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