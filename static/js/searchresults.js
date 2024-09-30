// Add directive to display search results

function addSearchResultsDirective(ngApp) {

    ngApp.directive('searchResults', ['SelectionService','SingleSelectionService', function(SelectionService,SingleSelectionService) {
        return {
            templateUrl: 'templates/search_results.html',
            scope: {
                searchResults: '=',
            },
            link: function(scope, elem, attr) {

                var sR = scope.searchResults;

                sR.max_results = sR.max_results || 20;
                sR.select_all_states = []; // Array to store select all states for each page

                sR.reset = function() {
                    sR.results = [];
                    sR.unwrapped_results = [];
                    sR.results_page = 0;     
                    sR.found_results = 0;
                    sR.search_complete = false;
                    sR.select_all_states = []; // Reset select all states
                    $('#search-scroll-container').scrollTop(0); // Reset scrolling
                }

                sR.reset();

                sR.change_page = function(i) {
                    sR.results_page += i;
                    sR.select_all = sR.select_all_states[sR.results_page] || false; // Restore select all state for new pages, retain state for previous selections
                    $('#search-scroll-container').scrollTop(0); // Reset scrolling
                }

                sR.update_results = function(results) {
                    sR.reset();
                    sR.unwrapped_results = results;
                    for (var i = 0; i < results.length; i += sR.max_results) {
                        sR.results.push(results.slice(i, i+sR.max_results));
                        sR.select_all_states.push(false); // Initialise select all state for each page
                    }
                    sR.search_complete = true;
                    sR.found_results = results.length;
                }

                // Use SelectionService to download selected items as zip archive
                sR.download_selected_zip = function() {
                    SelectionService.downloadSelectionZip();
                }

                // Use SelectionService to download selected items as a single JSON file
                sR.download_json = function() {
                    SelectionService.downloadSelectionJSON();
                }

                // Use SelectionService to download all results as a zip archive
                sR.download_all_zip = function() {
                    SelectionService.clearSelections();
                    for (var i = 0; i < sR.unwrapped_results.length; i++) {
                        sR.unwrapped_results[i].isChecked = true;
                        SingleSelectionService.singleSelection(sR.unwrapped_results[i]);
                    }
                    SelectionService.downloadSelectionZip();
                }
            }
        }
    }]);
}