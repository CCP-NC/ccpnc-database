function addUploadController(ngApp) {
    ngApp.controller('UploadController', function($scope, loginStatus, Upload) {

        var clearForm = function() {

            $scope.magres_file_name = '';
            $scope.magres_file = null; // Contents of the last uploaded file            
            $scope.uploading_now = false; // To show spinner if needed

            $('#upload-form').resetForm();

        }

        // Status message
        $scope.status = '';
        $scope.status_err = false; // Is the status an error?

        // Upload mode
        $scope.upload_multi = false;

        clearForm();

        $scope.upload = function() {

            // Check required fields
            $scope.status_err = false;
            $scope.status = '';
            $('#upload-form input[required]').each(function(i, o) {
                if ($(o).val() == '') {
                    $scope.status = 'Missing file or obligatory field';
                    $scope.status_err = true;
                }
            });
            if ($scope.status_err) {
                return;
            }

            // Compile extra data
            var request_data = {
                '_upload_multi': $scope.upload_multi
            };

            loginStatus.verify_token(function() {
                // Package all the data
                $.extend(request_data, loginStatus.get_ajax_id());

                // Post form
                $scope.uploading_now = true;
                $scope.$apply();
                $('#upload-form').ajaxSubmit({
                    data: request_data,
                    success: function(msg, status) {
                        // Did anything go wrong?
                        if (status != 'success') {
                            $scope.status = 'ERROR: ' + msg;
                            $scope.status_err = true;
                        } else {
                            $scope.status = 'Successfully uploaded';
                            $scope.status_err = false;
                            // Also, clear
                            clearForm();
                        }

                        $scope.uploading_now = false;
                        $scope.$apply();

                    },
                    error: function(err) {
                        $scope.status = 'ERROR: ' + err.responseText;
                        $scope.status_err = true;
                        $scope.uploading_now = false;
                        $scope.$apply();
                    }
                });

            }, function() {
                $scope.status = 'Could not authenticate ORCID details; '
                'please log in';
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
                $scope.magres_file_name = file.name;

                if (!$scope.upload_multi) {
                    var reader = new FileReader();
                    reader.onload = (function(fevent) {
                        var mtext = fevent.currentTarget.result;
                        $scope.uploading_now = false;
                        if (validateMagres(file.name, mtext)) {
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
                    reader.readAsText(file);
                }
            }
        }

        $scope.edit_additional = function() {
            $scope._edit_form = new editFormScope($scope);
        }

    });
}