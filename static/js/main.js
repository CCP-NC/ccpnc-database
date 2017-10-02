(function() {

  console.log('Creating Angular app...');
  var ccpncApp = angular.module('ccpncDatabaseApp', ['ngFileUpload']);

  // Create a service to hold login data
  ccpncApp.service('loginStatus', LoginStatus);

  // Add directives
  console.log('Loading directives...');
  addRecordDirective(ccpncApp);

  // Add controllers
  console.log('Loading controllers...');
  addNavigateController(ccpncApp);
  addLoginController(ccpncApp);
  addCookieLawController(ccpncApp);
  addUploadController(ccpncApp);
  addSearchController(ccpncApp);

  // Manual bootstrap (automatic one creates problem with order in which scripts are loaded)
  console.log('Bootstrapping app...');
  angular.element(function() {
      angular.bootstrap(document, ['ccpncDatabaseApp']);
  });
  console.log('Success');

})();