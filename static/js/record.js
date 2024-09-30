// Definitions for new directives

// Directive for database records
function addRecordDirective(ngApp) {

    ngApp.directive('databaseRecord', ['SelectionService', 'loginStatus', function(SelectionService,loginStatus) {
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

                scope.isadmin = function() {
                    return loginStatus.is_admin();
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

                            elem.find('.edit-popup-form').ajaxSubmit({
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

                scope.hideshow = function() {
                    // Show the hide confirmation popup
                    elem.find('#hide-confirm-modal').toggleClass('is-active');
                }

                scope.hide = function() {

                    // The record to hide
                    var request_data = {'_record_id': record_id};

                    loginStatus.verify_token(function() {

                        $.extend(request_data, loginStatus.get_ajax_id());

                        $.post(loginStatus.server_app + '/hide',
                               request_data,
                               function(data, status) {
                                    if (status != 'success') {
                                        alert('ERROR: ' + data);
                                    }
                                    else {
                                        alert('Record successfully hidden');
                                    }                                    
                                }
                        ).fail(function(e) {
                            alert('ERROR: ' + e.responseText);
                        }).always(function() {
                            scope.hideshow();
                        });

                    }, function() {
                        alert('User is not authorised to perform this operation')
                    }, true); // The last true means we check for admin status too

                }

                scope.filename = function() {
                    return 'MRD' + this.databaseRecord.immutable_id + 'v' + (parseInt(this._selected_index)+1);
                }

                scope.metadataJsonURI = function() {
                    var url = 'data:application/json;charset=utf-8,';
                    url += JSON.stringify(this.databaseRecord, null, 4);

                    return url;
                }

                scope.prettydate = function(date) {

                    // Prettify a date
                    var sdate = date.split(' ');
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

                scope.selectionChange = function(result) {
                    var target_val = result.last_version.magresFilesID;
                    var index_t = SelectionService.selectedItems.findIndex(item => item.fileID === target_val);
                    var filename = 'MRD' + result.immutable_id;
                    var version_num = (parseInt(result.version_count)-1); // version number of the selected item (latest version by default)
                    if (index_t > -1) {
                        SelectionService.selectedItems.splice(index_t, 1);
                    }
                    else {
                        SelectionService.selectedItems.push({fileID: target_val, filename: filename, jsonData: result, version: version_num});
                    }
                }

                scope.jsonRetrieve = function(result, version_num) {
                    SelectionService.clearSelections();
                    var target_val = result.version_history[version_num].magresFilesID;
                    var filename = scope.filename();
                    SelectionService.singleSelectJSON.push({fileID: target_val, filename: filename, jsonData: result, version: version_num});
                    SelectionService.downloadSelectionJSON();
                }
            }
        };
    }]);

}