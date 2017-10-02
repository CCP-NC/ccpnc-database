function addNavigateController(ngApp) {
    ngApp.controller('NavigateController', function($scope, loginStatus) {
        $scope.open_tab = '';
    });
}