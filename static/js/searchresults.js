// Add directive to display search results

function addSearchResultsDirective(ngApp) {

    ngApp.directive('searchResults', function() {
        return {
            templateUrl: 'templates/search_results.html',
            scope: {
                searchResults: '=',
            },
            link: function(scope, elem, attr) {

                var sR = scope.searchResults;

                sR.max_results = sR.max_results || 20;

                sR.reset = function() {
                    sR.results = [];
                    sR.results_page = 0;     
                    sR.found_results = 0;
                    sR.search_complete = false;
                }

                sR.reset();

                sR.change_page = function(i) {
                    sR.results_page += i;
                }

                sR.update_results = function(results) {
                    sR.results = [];
                    for (var i = 0; i < results.length; i += sR.max_results) {
                        sR.results.push(results.slice(i, i+sR.max_results));
                    }
                    sR.search_complete = true;
                    sR.found_results = results.length;
                }
            }
        }
    });

}