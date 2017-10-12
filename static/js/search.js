function addSearchController(ngApp) {
    ngApp.controller('SearchController', function($scope) {

        $scope.results = [
            {
                chemname: 'Generic Metallic Oxide',
                orcid: '00000001',
            },

            {
                title: 'Very Cool Zeolite',
                chemname: '00000002',
            },

        ];

    });
}