function addUploadController(ngApp) {
    ngApp.controller('UploadController', function($scope, loginStatus, Upload) {

        var clearForm = function() {
            $scope.magres_file_name = '';
            $scope.magres_file = null; // Contents of the last uploaded file            
            $scope.uploading_now = false; // To show spinner if needed

            $('#upload-form #chemname').val('');
            $('#upload-form #chemform').val('');

            for (var p in $scope._edit_table.get_props()) {
                $('#upload-form #edit-' + p).val('');
            }
        }

        // Form data
        $scope.chemname = '';

        // Status message
        $scope.status = '';
        $scope.status_err = false; // Is the status an error?        

        // Edit table
        $scope._edit_table = new editTable($scope, {});

        // Upload mode
        $scope.upload_multi = false;

        clearForm();

        $scope.upload = function() {

            if ($scope.magres_file == null) {
                $scope.status = 'No file to upload';
                $scope.status_err = true;
                return;
            }

            // Check obligatory details
            var request_data = {
                'upload_multi': $scope.upload_multi,
                'magres': $scope.magres_file,
                'chemname': $('#upload-form #chemname').val(),
                'form': $('#upload-form #chemform').val()
            };

            var obl = {
                'Chemical name': 'chemname'
            };

            for (var kname in obl) {
                if ($.trim(request_data[obl[kname]]) == '') {
                    $scope.status = kname + ' is obligatory';
                    $scope.status_err = true;
                    return;
                }
            }

            // Now add the optional information
            request_data = $.extend(request_data, $scope._edit_table.get_props());

            loginStatus.verify_token(function() {
                // Package all the data
                details = loginStatus.get_details()
                request_data.access_token = details['access_token'];
                request_data.orcid = details['orcid'];

                // Send an Ajax request
                $scope.uploading_now = true;
                $scope.$apply();

                $.ajax({
                    url: ngApp.server_app + '/upload',
                    type: 'POST',
                    crossDomain: true,
                    data: request_data
                }).done(function(r) {
                    // Did anything go wrong?
                    if (r != 'Success') {
                        $scope.status = 'ERROR: ' + r;
                        $scope.status_err = true;
                    } else {
                        $scope.status = 'Successfully uploaded';
                        $scope.status_err = false;
                        // Also, clear
                        clearForm();
                    }

                    $scope.uploading_now = false;
                    $scope.$apply();

                }).fail(function(e) {
                    $scope.status = e;
                    $scope.status_err = true;
                    $scope.uploading_now = false;
                    $scope.$apply();
                });

            }, function() {
                $scope.status = 'Could not authenticate ORCID details; please log in'
                $scope.status_err = true;
            });
        }

        $scope.load_files = function(files) {
            // Must be only one file for now
            if (files.length != 1) {
                $scope.status = 'Only one file can be uploaded at a time';
                $scope.status_err = true;
                return;
            } else {
                var file = files[0];
                $scope.status = '';
                $scope.status_err = false;

                var reader = new FileReader();
                reader.onload = (function(fevent) {
                    var mtext = fevent.currentTarget.result;
                    $scope.uploading_now = false;
                    if ($scope.upload_multi || validateMagres(file.name, mtext)) {
                        $scope.magres_file_name = file.name;
                        $scope.magres_file = mtext;
                        $scope.status_err = false;
                        $scope.status = 'File ready to upload';
                    } else {
                        $scope.magres_file_name = '';
                        $scope.magres_file = null;
                        $scope.status_err = true;
                        $scope.status = 'The file is not in the Magres format';
                    }
                    $scope.$apply();
                });
                $scope.uploading_now = true;
                if ($scope.upload_multi) {
                    reader.readAsArrayBuffer(file);
                } else {
                    reader.readAsText(file);
                }
            }
        }

        $scope.edit_additional = function() {
            $scope._edit_form = new editFormScope($scope);
        }

    });
}