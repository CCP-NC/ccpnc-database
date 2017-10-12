function addUploadController(ngApp) {
    ngApp.controller('UploadController', function($scope, loginStatus, Upload) {

        var clearMagres = function() {
            $scope.magres_file_name = '';
            $scope.magres_file = null; // Contents of the last uploaded file            
            $scope.uploading_now = false; // To show spinner if needed

            $('#upload-form #chemname').val('');
            $('#upload-form #doi').val('');
            $('#upload-form #notes').val('');

        }

        clearMagres();

        // Form data
        $scope.chemname = '';

        // Status message
        $scope.status = '';
        $scope.status_err = false; // Is the status an error?        

        $scope.upload = function() {

            if ($scope.magres_file == null) {
                $scope.status = 'No file to upload';
                $scope.status_err = true;
                return;
            }

            // Check obligatory details
            var data = {
                    'magres': $scope.magres_file,
                    'chemname': $('#upload-form #chemname').val(),
                    'doi': $('#upload-form #doi').val(),
                    'notes': $('#upload-form #notes').val(),
            };

            var obl = {'Chemical name': 'chemname'};

            for (var kname in obl) {
                if ($.trim(data[obl[kname]]) == '') {
                    $scope.status = kname + ' is obligatory';
                    $scope.status_err = true;
                    return;
                }
            }                


            loginStatus.verify_token(function() {
                // Package all the data
                details = loginStatus.get_details()
                data.access_token = details['access_token'];
                data.orcid = details['orcid'];

                // Send an Ajax request
                $scope.uploading_now = true;
                $scope.$apply();

                $.ajax({
                    url: '/upload',
                    type: 'POST',
                    crossDomain: true,
                    data: data
                }).done(function(r) {
                    // Did anything go wrong?
                    if (r != 'Success') {                        
                        $scope.status = 'ERROR: ' + r;
                        $scope.status_err = true;
                    }
                    else {
                        $scope.status = 'Successfully uploaded';
                        $scope.status_err = false;                    
                        // Also, clear
                        clearMagres();
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
                    if (validateMagres(file.name, mtext)) {
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
                reader.readAsText(file);
            }
        }

    });
}