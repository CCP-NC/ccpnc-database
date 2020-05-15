function addNavigateController(ngApp) {
    ngApp.controller('NavigateController', function($scope, loginStatus) {
        $scope.open_tab = '';
        $scope.loginStatus = loginStatus;

        $scope.menu_display = false;
        $scope.show_menu_mobile = function() {
            $scope.menu_display = !$scope.menu_display;
        }

        // Is there any record MDBREF in the url parameters?
        var sp = new URLSearchParams(window.location.search.slice(1));
        $scope.recordref = sp.get('mdbref');

    });
}