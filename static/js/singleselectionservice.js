function addSingleSelectionService(ngApp) {

    ngApp.service('SingleSelectionService', ['$http','SelectionService', function($http, SelectionService) {
        this.singleSelection = function (result) {
            
            var target_val = result.last_version.magresFilesID; // target value - string containing the Magres fileID
            var index_t = SelectionService.selectedItems.findIndex(item => item.fileID === target_val); // index of target value in selectedItems array
            
            var filename = 'MRD' + result.immutable_id; // string to be used as filename
            var version_num = (parseInt(result.version_count)-1); // version number of the selected item
            // if the checkbox is checked and the target value is not in the selectedItems array, add the target value to the selectedItems array
            // else if the checkbox is unchecked and the target value is in the selectedItems array, remove the target value from the selectedItems array
            if (result.isChecked) {
                if (index_t === -1) {
                    SelectionService.selectedItems.push({ fileID: target_val, filename: filename, jsonData: result, version: version_num});
                }
            } else {
                if (index_t > -1) {
                    SelectionService.selectedItems.splice(index_t, 1);
                }
            }
        }
    }]);
}