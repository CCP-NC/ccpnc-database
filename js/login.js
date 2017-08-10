function addLoginController(ngApp) {

    // Change this depending on where the server app is located
    login_server_app = 'http://localhost:8080';
    // And this depending on where the orcid login is
    login_orcid = 'https://sandbox.orcid.org/oauth/authorize';
    // Public app data
    app_data = {
        'client_id': 'APP-6E61LI8HDS1P897J',
        'response_type': 'code',
        'scope': '/authenticate',
        'redirect_uri': 'http://localhost:8000'
    };

    ngApp.controller('LoginController',
        function LoginController($scope) {

            // If the details are already kept in localStorage, use those
            // If not, then this returns null, which is the default for not having a log in
            $scope.details = JSON.parse(window.localStorage.getItem('login_details'));

            /* Upon creation, we need to check if there's a code in the URL's query
            and in case retrieve the tokens as necessary */
            var sp = new URLSearchParams(window.location.search.slice(1));
            var code = sp.get('code');
            if (code != null) {
                $.ajax({
                    url: login_server_app + '/gettokens/' + code,
                    type: "GET",
                    crossDomain: true,
                    success: function (response) {
                        var resp = JSON.parse(response);
                        // Did it succeed?
                        if ('error' in resp) {
                            console.log('ORCID login error:');
                            console.log(resp.error_description);
                            return;
                        }
                        // If we're here, we're good!
                        $scope.details = resp;                
                        $scope.$applyAsync();       
                        window.localStorage.setItem('login_details', response);

                    },
                    error: function (xhr, status) {
                        console.log('A SERVER SIDE ERROR HAS VERIFIED:');
                        console.log(status);
                    }
                });
            }

            $scope.login = function() {
                // Navigate to the login ORCID URL
                var u = new URL(login_orcid);
                var usp = new URLSearchParams();
                for (var k in app_data) {
                    usp.append(k, app_data[k]);
                }
                u.search = '?' + usp.toString();
                // And go there!
                window.location.replace(u.href);                
            }

            $scope.logout = function() {
                // Delete the tokens locally
                window.localStorage.removeItem('login_details');
                // Delete the tokens from the scope
                $scope.details = null;
                // Delete the cookies
                $.ajax({
                    url: login_server_app + '/logout',
                    type: "GET",
                    crossDomain: true
                });
                // Log out from ORCID
                $.ajax({
                    url: 'https://sandbox.orcid.org/userStatus.json?logUserOut=true',
                    dataType: 'jsonp',
                    success: function(result,status,xhr) {
                        console.log('Logged In: ' + result.loggedIn);
                    },
                    error: function (xhr, status, error) {
                        console.log('Error: ' + status);
                    }
                });

            }

        });
}