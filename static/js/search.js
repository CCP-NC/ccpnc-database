function parseSearchResults(s) {
    // Try parsing as JSON; if not, print as error message
    results = null;

    try {
        results = JSON.parse(s);
    } catch (e) {
        console.log(s);
    }

    return results
}

function addSearchController(ngApp) {

    ngApp.controller('SearchController', function($scope) {

        $scope.message = '';

        $scope.search_specs = [];

        $scope.add_spec = function() {
            $scope.search_specs.push({
                'type': 'doi',
                'args': {}
            });
            $scope.search_complete = false;
        }

        $scope.remove_spec = function(i) {
            if ($scope.search_specs.length > 1)
                $scope.search_specs.splice(i, 1);
        }

        $scope.reset_search_args = function(new_type) {
            $scope.search_complete = false;
            $scope.search_args = {};
        }

        $scope.max_results = 20;

        $scope.add_spec();
        $scope.search_results = [];
        $scope.results_page = 0;
        $scope.search_complete = false;

        var last_query = null;

        $scope.search = function() {
            $scope.message = '';
            query = {
                url: ngApp.server_app + '/search',
                type: 'POST',
                crossDomain: true,
                contentType: 'application/json',
                data: JSON.stringify({
                    'search_spec': $scope.search_specs
                }),
                success: function(d, statusText, xhr) {
                    var results = parseSearchResults(d)

                    $scope.message = '';

                    if (results == null) {
                        // Should NEVER happen, but you never know...
                        $scope.message = 'An unknown error has occurred';
                    }
                    else {                        
                        // Cap max results
                        $scope.search_results = [];
                        for (var i = 0; i < results.length; i += $scope.max_results) {
                            $scope.search_results.push(results.slice(i, i+$scope.max_results));
                        }
                    }

                    $scope.search_complete = true;
                    $scope.$apply();
                },
                error: function(xhr, statusText) {
                    switch (xhr.status) { // Return more understandable errors
                        case 400:
                            $scope.message = 'Search parameters missing or invalid';
                            break;
                        default:
                            $scope.message = 'An unknown error has occurred';
                            break;
                    }
                    $scope.$apply();
                }
            }

            $.ajax(query);
            last_query = query;
        }

        $scope.refresh = function() {
            // Just repeat the last query
            if (last_query) {
                $.ajax(last_query);
            }
        }

        $scope.change_page = function(i) {
            $scope.results_page += i;
        }

    });
}