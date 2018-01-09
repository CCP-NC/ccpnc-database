// Handles the list of files uploaded by the user, searched by ORCID
function addFileListerController(ngApp) {

    ngApp.controller('FileListerController', function($scope, loginStatus) {

        // This code gets executed every time the tab is opened, and refreshes
        // the contents

        details = loginStatus.get_details();

        // Perform a search for files with same ORCID
        query =  {
            url: '/search', 
            type: 'POST', 
            crossDomain: true, 
            contentType: 'application/json', 
            data: JSON.stringify({'search_spec': [{
                'type': 'orcid',
                'orcid': details.orcid,
                },]
            })
        }

        $.ajax(query).done(function(d) {
            $scope.search_results = parseSearchResults(d);
            //console.log($scope.search_results);
            $scope.$apply();
        });

    });
}