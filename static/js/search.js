function parseSearchResults(s) {
    // Try parsing as JSON; if not, print as error message
    results = null;

    try {
        results = JSON.parse(s);
    }
    catch (e) {
        console.log(s);
    }

    return results
}

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

        $scope.message = '';

        $scope.search_specs = [];

        $scope.add_spec = function() {
            $scope.search_specs.push({
                'type': 'doi'
            });
        }

        $scope.remove_spec = function(i) {
            if ($scope.search_specs.length > 1)
                $scope.search_specs.splice(i, 1);
        }

        $scope.reset_search_args = function(new_type) {
            $scope.search_args = {};
            for (var argname in searchTypes[new_type]) {
                $scope.search_args[argname] = null;
            }
        }

        $scope.server_app = 'https://www.ccpnc.ac.uk/database'

        $scope.add_spec();
        $scope.search_results = [];

        $scope.search = function() {
            // For now just a test thing to keep in mind how it's done
            $scope.message = '';
            
            query =  {
                url: $scope.server_app + '/search', 
                type: 'POST', 
                crossDomain: true, 
                contentType: 'application/json', 
                data: JSON.stringify({'search_spec': $scope.search_specs
                                    })
            }

            $.ajax(query).done(function(d) {
                $scope.search_results = parseSearchResults(d);
                if ($scope.search_results == null) {
                    var errcode = parseInt(d.match(/\d+/)[0]);
                    switch(errcode) { // Return more understandable errors
                        case 400:
                            $scope.message = 'Search parameters missing or invalid';
                            break;
                        default:
                            $scope.message = 'An unknown error has happened';
                            break;
                    }
                }
                $scope.$apply();
            });
        }

    });
}
