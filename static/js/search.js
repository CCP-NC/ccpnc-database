function addSearchController(ngApp) {

    /* SEARCH TYPES and arguments */
    var searchTypes = {
        'doi': {
            'doi': String,
        },
        'msRange': {
            'sp': String,
            'minms': parseFloat,
            'maxms': parseFloat
        }
    }

    ngApp.controller('SearchController', function($scope) {

        $scope.search_type = 'doi';

        $scope.reset_search_args = function(new_type) {
            $scope.search_args = {};
            for (var argname in searchTypes[new_type]) {
                $scope.search_args[argname] = null;
            }
        }

        $scope.reset_search_args($scope.search_type); // Init

        $scope.search_results = [{
            'chemname': 'Ethanol',
            'doi': '10.1000'
        }];

        $scope.search = function() {
            // For now just a test thing to keep in mind how it's done
            search_spec = [];
            search_data = {
                'type': $scope.search_type
            };
            for (var argname in $scope.search_args) {
                if ($scope.search_args[argname] != null)
                    search_data[argname] = $scope.search_args[argname];
                else {                    
                    console.log('Error');
                    return;
                }
            }
            search_spec.push(search_data);

            query =  {
                url: '/search', 
                type: 'POST', 
                crossDomain: true, 
                contentType: 'application/json', 
                data: JSON.stringify({'search_spec': search_spec
                                    })
            }

            $.ajax(query).done(function(d) {
                $scope.search_results = d;
                $scope.$apply();
                console.log($scope.search_results);
            });
        }

    });
}