$(function() {
    var show = true;
    $('.list').hide();
    $('#username').click(
        function() {
            if (show) {
                $('.list').slideDown();
                show = false;
            }
            else {
                $('.list').slideUp();
                show = true;
            }
        }
    )
});