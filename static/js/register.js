$(function() {
    $('.alert').hide();
    $('#confirm-alert').hide();
    $('#enter-button').click(function() {
        var submit_ok = true;
        if (!$('.username-form').val()) {
            $('#username-form .alert').show();
            submit_ok = false;
        }else {
            $('#username-form .alert').hide();
        }
        if (!$('.password-form').val()) {
            $('#password-form .alert').show();
            submit = false;
        }else {
            $('#password-form .alert').hide();
        }
        if (!$('.confirmpassword-form').val()) {
            $('#confirmpassword-form .alert').show();
            submit_ok = false;
        }else {
            if ($('.confirmpassword-form').val() != $('.password-form').val()) {
                $('#confirm-alert').show();
                submit_ok = false;
            }else {
                $('#confirm-alert').hide();
            }
        }
        if(!$('.email-form').val()) {
            $('#email-form .alert').show();
        }else {
            $('#email-form .alert').hide();
        }
        if (submit_ok == false) {
            $('.login-form').submit(function(event) {
                event.preventDefault();
            });
        }
    });
});