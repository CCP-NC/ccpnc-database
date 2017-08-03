// Initialise navigation links
(function() {

    function hide_all(except) {
        $('.main-section').not(except).addClass('hidden');
    }

    $('.navbar-menu .navbar-item').each(function(i, item) {
        item = $(item);
        var target = item.data('target');
        if (target == null)
            return;
        item.click(function() {
            hide_all();
            $('#' + target).removeClass('hidden');
        });
    });

    hide_all('#div-home');

})();