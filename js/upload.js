function addUploadController(ngApp) {
    ngApp.controller('UploadController', function($scope, loginStatus) {

        $scope.upload = function() {
            loginStatus.verify_token(function() {
                console.log('YAY!');
            });
        }

    });
}