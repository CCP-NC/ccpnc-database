function addLoginController(ngApp) {

    ngApp.controller('LoginController', 
                    function LoginController($scope) {
        $scope.logged_in = false;
        $scope.user = null;

        $scope.login = function() {
          $scope.logged_in = true;
        }

        $scope.logout = function() {
          $scope.logged_in = false;
        }

    });
}