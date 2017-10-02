function addSearchController(ngApp) {
    ngApp.controller('SearchController', function($scope) {

        $scope.results = [
            {
                title: 'Generic Metallic Oxide',
                orcid: '00000001',
            },

            {
                title: 'Very Cool Zeolite',
                orcid: '00000002',
            },

        ];

    });
}