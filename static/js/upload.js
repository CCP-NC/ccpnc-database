function addUploadController(ngApp) {
    ngApp.controller('UploadController', function($scope, loginStatus, Upload) {

        $scope.magres_file = null; // Contents of the last uploaded file

        // Form data
        $scope.chemname = '';

        // Status message
        $scope.status = '';
        $scope.status_err = false; // Is the status an error?

        $scope.upload = function() {
            if ($scope.magres_file == null) {
                $scope.status = 'No file to upload';
                $scope.status_err = true;
            }
            loginStatus.verify_token(function() {
                console.log($scope.chemname);
                // Package all the data
                details = loginStatus.get_details()
                data = {
                        'magres': $scope.magres_file,
                        'chemname': $('#upload-form #chemname').val(),
                        'doi': $('#upload-form #doi').val(),
                        'notes': $('#upload-form #notes').val(),
                        'access_token': details['access_token'],
                        'orcid': details['orcid']
                    };
                    // Send an Ajax request
                var r = $.ajax({
                    url: '/upload',
                    type: 'POST',
                    crossDomain: true,
                    data: data
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
                    if (validateMagres(file.name, mtext)) {
                        $scope.magres_file = mtext;
                        $scope.status_err = false;
                        $scope.status = file.name;
                    } else {
                        $scope.status_err = true;
                        $scope.status = 'The file is not in the Magres format';
                    }
                });
                reader.readAsText(file);
            }
        }

        $scope.show_warning = function(msg, is_err) {

            var ue = $('.upload-error');

            if (msg == null) {
                ue.addClass('is-hidden');
            } else if (!is_err) {
                ue.html(msg);
                ue.removeClass('has-text-danger');
                ue.addClass('has-text-success');
                ue.removeClass('is-hidden');
            }
        }

    });
}