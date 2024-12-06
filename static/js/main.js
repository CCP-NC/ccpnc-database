(function() {

  console.log('Creating Angular app...');
  var ccpncApp = angular.module('ccpncDatabaseApp', ['ngFileUpload']);

  // Assign some app-wide configuration constants
  ccpncApp.server_app = ccpnc_config.server_app;
  ccpncApp.redirect_uri = ccpnc_config.redirect_uri;

  // Create a service to hold login data
  console.log('Launching login service...');
  ccpncApp.service('loginStatus', LoginStatus);

  // Add directives
  console.log('Loading directives...');
  addTemplateDirectives(ccpncApp);
  addRecordDirective(ccpncApp);
  addEditPopupDirective(ccpncApp);
  addSearchResultsDirective(ccpncApp);

  // Add controllers
  console.log('Loading controllers...');
  addNavigateController(ccpncApp);
  addLoginController(ccpncApp);
  addCookieLawController(ccpncApp);
  addUploadController(ccpncApp);
  addSearchController(ccpncApp);
  addMailController(ccpncApp);
  addFileListerController(ccpncApp);
  addRecordController(ccpncApp);

  //Add services
  console.log('Loading services...');
  addSelectionService(ccpncApp);
  addSingleSelectionService(ccpncApp);
  addAuthorsService(ccpncApp);

  // Manual bootstrap (automatic one creates problem with order in which scripts are loaded)
  console.log('Bootstrapping app...');
  angular.element(function() {
      angular.bootstrap(document, ['ccpncDatabaseApp']);
  });
  console.log('Success');

})();