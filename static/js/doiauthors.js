function addAuthorsService(ngApp) {

    ngApp.service('DoiAuthorsService', ['$http', function($http) {

        // Ensure ccpnc_config is defined when loading js/config.js into index.html
        if (typeof ccpnc_config === 'undefined') {
            console.error('ccpnc_config is not defined');
            return;
        }

        const apiBaseUrl = ccpnc_config.server_app;

        var service = {
            getAuthorInfo: function(doi) {
                return $http.get(`${apiBaseUrl}/api/works`, { params: { doi: doi } })
                    .then(function(response) {
                        return response.data;
                    })
                    .catch(function(error) {
                        console.error('Error fetching author information:', error);
                        return 'Error fetching author information';
                    });
        }
    };
    
    return service;
}]);
}