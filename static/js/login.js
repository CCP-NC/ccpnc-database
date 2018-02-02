// Definition of the LoginStatus service object
var LoginStatus = function() {
    this.server_app = ccpnc_config.server_app;
};

LoginStatus.prototype = {

    parse_response_tokens: function(response) {
        var resp = JSON.parse(response);
        // Did it succeed?
        if (resp != null && 'error' in resp) {
            console.log('ORCID login error:');
            console.log(resp.error_description);
            return null;
        }
        // If we're here, we're good!
        return resp;
    },

    request_tokens: function(code, success, error) {

        success = success || function(response) {
            return;
        };
        error = error || function(xhr, status) {
            console.log('A SERVER SIDE ERROR HAS VERIFIED:');
            console.log(status);
        };

        url = this.server_app + '/gettokens/';

        if (code != null)
        {
            console.log('Requesting tokens for code ' + code);
            url += code;
        }

        $.ajax({
            url: url,
            type: "GET",
            crossDomain: true,
            success: success,
            error: error
        });

    },

    remove_cookies: function() {
        // Delete the cookies
        $.ajax({
            url: ccpnc_config.server_app + '/logout',
            type: "GET",
            crossDomain: true
        });
    },

    set_details: function(details) {
        window.localStorage.setItem('login_details', JSON.stringify(details));
    },

    get_details: function() {
        var details = window.localStorage.getItem('login_details');
        return JSON.parse(details);
    },

    remove_details: function() {
        window.localStorage.removeItem('login_details');
    },

    get_login_status: function() {
        return window.localStorage.hasOwnProperty('login_details');
    },

    verify_token: function(success, error) {

        error = error || function() {
            console.log('TOKENS COULD NOT BE VERIFIED');
        };

        // Verify the locally stored token vs. the one in cookies
        var local_token = this.get_details();
        if (local_token == null) {
            error();
            return;
        }
        local_token = local_token.access_token;

        // Now get the remote one
        var that = this;
        this.request_tokens(null, function(response) {            
            var cookie_token = that.parse_response_tokens(response);
            if (cookie_token == null) {
                error();
                return;
            }
            cookie_token = cookie_token.access_token;

            if (cookie_token === local_token) {
                success();
                return;
            }
            else {
                error();
                return;
            }
        },
        error);
    }

};

// This function adds the login controller to the passed app
function addLoginController(ngApp) {

    // Change this depending on where the orcid login is
    login_orcid = 'https://orcid.org/';
    // Public app data
    app_data = {
        'client_id': 'APP-KV1OV8U12GT9FTQR',
        'response_type': 'code',
        'scope': '/authenticate',
        'redirect_uri': ngApp.redirect_uri
    };

    ngApp.controller('LoginController',
        function LoginController($scope, loginStatus) {

            $scope.logged_in = false;
            $scope.just_logged_in = false;
            $scope.username = '';
            $scope.orcid = '';

            function update_details(details) {

                $scope.logged_in = (details != null);
                $scope.username = ($scope.logged_in ? details.name : '');
                $scope.orcid = ($scope.logged_in ? details.orcid : '');
                $scope.$applyAsync();

                if (details != null) {
                    loginStatus.set_details(details);
                } else {
                    loginStatus.remove_details();
                    loginStatus.remove_cookies();
                }
            }

            // If the details are already kept in localStorage, use those
            // If not, then this returns null, which is the default for not having a log in
            update_details(loginStatus.get_details());

            /* Upon creation, we need to check if there's a code in the URL's query
            and in case retrieve the tokens as necessary */
            var sp = new URLSearchParams(window.location.search.slice(1));
            var code = sp.get('code');
            if (code != null) {
                loginStatus.request_tokens(code, function(response) {
                    resp = loginStatus.parse_response_tokens(response);
                    if (resp == null) {
                        return;
                    }
                    update_details(resp);
                    // And if possible reset the location

                    try {
                        window.history.pushState({
                                path: window.location.origin+window.location.pathname
                            }, '',
                            window.location.origin+window.location.pathname)
                    } catch (e) {
                        console.log(e);
                    }

                    $scope.just_logged_in = $scope.logged_in;
                });
            }

            $scope.login = function() {
                // Navigate to the login ORCID URL
                var u = new URL(login_orcid + 'oauth/authorize');
                var usp = new URLSearchParams();
                for (var k in app_data) {
                    usp.append(k, app_data[k]);
                }
                u.search = '?' + usp.toString();
                // And go there!
                window.location.replace(u.href);
            }

            $scope.logout = function() {
                // Delete the tokens from the scope, localStorage,
                // and cookies
                update_details(null);
                // Log out from ORCID
                $.ajax({
                    url: login_orcid + 'userStatus.json?logUserOut=true',
                    dataType: 'jsonp',
                    success: function(result, status, xhr) {
                        console.log('Logged In: ' + result.loggedIn);
                    },
                    error: function(xhr, status, error) {
                        console.log('Error: ' + status);
                    }
                });

            }

            $scope.confirm = function() {
                // Make the confirm popup disappear
                $scope.just_logged_in = false;
            }

        });
}
