function addAuthorsService(ngApp) {

    ngApp.service('DoiAuthorsService', ['$http', '$sce', function($http, $sce) {

        // Ensure ccpnc_config is defined when loading js/config.js into index.html
        if (typeof ccpnc_config === 'undefined') {
            console.error('ccpnc_config is not defined');
            return;
        }

        const apiBaseUrl = ccpnc_config.server_app;
        const requestTimeout = 10000; // 10 seconds timeout
        const maxRetries = 2; // Number of retries

        var service = {
            getAuthorInfo: function(doi) {
                return makeRequest(doi, maxRetries);
            }
        };

        function makeRequest(doi, retries) {
            return $http({
                method: 'GET',
                url: `${apiBaseUrl}/get_authors`,
                params: { doi: doi },
                timeout: requestTimeout
            })
            .then(function(response) {
                return $sce.trustAsHtml(response.data);
            })
            .catch(function(error) {
                if (error.status === 404) {
                    console.error('DOI not found:', error);
                    return $sce.trustAsHtml('DOI not found on Crossref. Please check the DOI again.');
                } else if (retries > 0) {
                    console.warn(`Retrying... (${maxRetries - retries + 1}/${maxRetries})`);
                    return makeRequest(doi, retries - 1);
                } else if (error.status === -1) {
                    console.error('Request timed out.');
                    return $sce.trustAsHtml('Request timed out. Please try again later.');
                }
            });
        }
    
    return service;
}]);
}