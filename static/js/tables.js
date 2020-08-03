// Add directives necessary to use templates

function addTemplateDirectives(ngApp) {

    ngApp.directive('recordTable', function() {
        return {
            templateUrl: 'templates/record_table.html',
            scope: {
                recordTable: '=',
            },
        }
    });

    ngApp.directive('versionTable', function() {
        return {
            templateUrl: 'templates/version_table.html',
            scope: {
                versionTable: '=',
            },
        }
    });
}