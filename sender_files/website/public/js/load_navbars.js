$(document).ready(function () {
    'use strict';
    $('#navbar-wrapper').load('/static/common/navbar.html', function () {
        $('#sidebar-wrapper').load('/static/common/sidebar.html', function () {
            $('#menu ul').hide();
            $('#menu ul').children('.current').parent().show();
            //$('#menu ul:first').show();

            $("#menu-toggle").click(function (e) {
                e.preventDefault();
                $("#wrapper").toggleClass("toggled");
            });
            $("#menu-toggle-2").click(function (e) {
                e.preventDefault();
                $("#wrapper").toggleClass("toggled-2");
                if ($("#wrapper").hasClass("toggled-2")) {
                    $("#menu li ul").css("padding-left", 0);
                } else {
                    $("#menu li ul").css("padding-left", 40);
                }
                //Collapse pills when sidebar changes
                //$('#menu ul').hide();
            });
            //menu li nav-pills
            $('#menu li a').click(function () {
                var checkElement = $(this).next();
                if (checkElement.is('ul')) {
                    $("#menu li").removeClass("active");
                    if ((checkElement.is(':visible'))) {
                        $('#menu ul:visible').slideDown('normal');
                        checkElement.slideUp('normal');
                        return false;
                    } else {
                        $(this).parent("li").addClass("active");
                        $('#menu ul:visible').slideUp('normal');
                        checkElement.slideDown('normal');
                        return false;
                    }
                }
            });

        });
    });
});
