function addNavigateController(ngApp) {
    ngApp.controller('NavigateController', function($scope, loginStatus) {
        $scope.open_tab = '';
        $scope.loginStatus = loginStatus;

        var obj = {a: 'x', b: 'Hello '};
        $scope.things = [obj, {b: 'Duh '}];
    });
}