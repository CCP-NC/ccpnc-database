// Handles the list of files uploaded by the user, searched by ORCID
function addFileListerController(ngApp) {

    ngApp.controller('FileListerController', function($scope, loginStatus) {

        $scope.message = '';
        $scope.search_results = {
            max_results: 20
        };

        // This code gets executed every time the tab is opened, and refreshes
        // the contents

        details = loginStatus.get_details();

        // Perform a search for files with same ORCID
        query = {
            url: ngApp.server_app + '/search',
            type: 'POST',
            crossDomain: true,
            contentType: 'application/json',
            data: JSON.stringify({
                'search_spec': [{
                    'type': 'orcid',
                    'args': {
                        'orcid': details.orcid,
                    },
                }, ]
            }),
            success: function(d, statusText, xhr) {
                $scope.search_results.update_results(parseSearchResults(d));
                $scope.message = '';
                $scope.$apply();
            },
            error: function(xhr, statusText) {
                $scope.message = 'ERROR: connection failed - ' + xhr.statusText;
                $scope.$apply();
            },
            timeout: 1000
        };

        $scope.refresh = function() {
            $.ajax(query);
        }
    });
}
