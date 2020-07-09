function addMailController(ngApp) {
    ngApp.controller('MailController', function($scope) {

        $scope.form = {
            email: ''
        };

        $scope.sendmail = function() {
            $('#contact-form').ajaxSubmit({
                success: function(msg, status) {

                },
                error: function(err) {
                    
                }
            });
        };
    });
}