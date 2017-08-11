// This function adds the cookie law controller to the passed app
function addCookieLawController(ngApp) {

    ngApp.controller('CookieLawController', function($scope) {

        $scope.approved = Boolean(window.sessionStorage.getItem('cookies_approved') || false);

        $scope.approve = function() {
            $scope.approved = true;
            window.sessionStorage.setItem('cookies_approved', true);
        }


    });

}