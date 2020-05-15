function addRecordController(ngApp) {
    ngApp.controller('RecordController', function($scope, loginStatus) {
        var mdbref = $scope.recordref;

        $scope.found = false;

        // Retrieve immediately all relevant information
        query = {
            url: ngApp.server_app + '/get_record',
            type: 'POST',
            crossDomain: true,
            contentType: 'application/json',
            data: JSON.stringify({
                'mdbref': mdbref
            }),
            success: function(d, statusText, xhr) {
                $scope.record = JSON.parse(d);
                $scope.found = true;
                $scope.$apply();
            },
            error: function(xhr, statusText) {
                switch (xhr.status) { // Return more understandable errors
                    case 400:
                        $scope.record = null;
                        break;
                    default:
                        break;
                }
                $scope.$apply();
            }
        }

        $.ajax(query);
    });
}