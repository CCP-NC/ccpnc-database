function addSearchController(ngApp) {
    ngApp.controller('SearchController', function($scope) {

        $scope.results = [
            {
                chemname: 'Generic Metallic Oxide',
                orcid: '00000001',
            },

            {
                title: 'Very Cool Zeolite',
                chemname: '00000002',
            },

        ];

        $scope.search = function() {
            // For now just a test thing to keep in mind how it's done
            query =  {
                url: '/search', 
                type: 'POST', 
                crossDomain: true, 
                contentType: 'application/json', 
                data: JSON.stringify({'search_spec': [{'type': 'msRange', 
                                                       'sp': 'C', 
                                                       'minms': 30, 
                                                       'maxms': 200}]
                                    })
            }

            $.ajax(query).done(function(d) {
                console.log(d);
            });
        }

    });
}