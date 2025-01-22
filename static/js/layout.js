$(function() {
    $('#username').hover(
        function() {
            $('.list').show();
        },
        function() {
            $('.list').hide();
        }
    )
    $('.list').hover(
        function() {
            $('.list').show();
        }
    )
});