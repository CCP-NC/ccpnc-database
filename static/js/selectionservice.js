function addSelectionService(ngApp) {

    ngApp.service('SelectionService', ['$http', function($http) {
        // This service is used to store the selected items in the selection page and to download the selected items 
        // as a zip archive or a single JSOn file depending on user selection
        var service = {
            selectedItems: [],
            singleSelectJSON: [],

            //Method to clear the selectedItems array
            clearSelections: function() {
                this.selectedItems.length = 0; //clear the array
                this.singleSelectJSON.length = 0;
            },
            //Method to create a zip archive of the selected items for download
            downloadSelectionZip: function() {
                $http.post('/download_selection_zip', { files: this.selectedItems }, { responseType: 'arraybuffer' })
                    .then(function(response) {
                        var blob = new Blob([response.data], { type: 'application/zip' });
                        var downloadUrl = window.URL.createObjectURL(blob);
                        var link = document.createElement('a');
                        link.href = downloadUrl;
                        link.download = 'selected_files.zip';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        window.URL.revokeObjectURL(downloadUrl);
                    })
                    .catch(function(error) {
                        console.error('Error downloading selection:', error);
                    });
            },
            //Method to create a single JSON file of the selected record metadata for download
            downloadSelectionJSON: function() {
                $http.post('/download_selection_json', { files: this.singleSelectJSON }, { responseType: 'json' })
                    .then(function(response) {
                        var jsonStr = JSON.stringify(response.data, null, 2);
                        var blob = new Blob([jsonStr], { type: 'application/json' });
                        var downloadUrl = window.URL.createObjectURL(blob);
                        var link = document.createElement('a');
                        link.href = downloadUrl;
                        link.download = this.singleSelectJSON[0].filename + '.json';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        window.URL.revokeObjectURL(downloadUrl);
                    }.bind(this))
                    .catch(function(error) {
                        console.error('Error downloading JSON:', error);
                    });
            }
        };

        return service;

    }]);

}