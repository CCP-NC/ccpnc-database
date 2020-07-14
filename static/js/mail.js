function addMailController(ngApp) {
    ngApp.controller('MailController', function($scope) {

        $scope.form = {
            email: ''
        };

        $scope.status = '';
        $scope.status_err = false;

        $scope.sendmail = function() {
            $('#contact-form').ajaxSubmit({
                success: function(msg, status) {
                    $scope.status = 'Message sent successfully';
                    $scope.status_err = false;
                    $scope.$apply();
                    $('#contact-form')[0].reset();
                },
                error: function(err) {
                    $scope.status = err.responseText;
                    $scope.status_err = true;
                    $scope.$apply();
                }
            });
        };
    });
}