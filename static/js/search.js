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
                'type': 'doi',
                'args': {}
            });
        }

        $scope.remove_spec = function(i) {
            if ($scope.search_specs.length > 1)
                $scope.search_specs.splice(i, 1);
        }

        $scope.reset_search_args = function(new_type) {
            $scope.search_args = {};
        }

        $scope.add_spec();
        $scope.search_results = [];

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
                    $scope.search_results = parseSearchResults(d);
                    if ($scope.search_results == null) {
                        // Should NEVER happen, but you never know...
                        $scope.message = 'An unknown error has occurred';
                    }
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

    });
}