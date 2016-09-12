$(document).ready(function () {
    'use strict';

    /* Load the top navbar, and then when that's done load the sidebar. These
     * are dynamically loaded in because all of the pages require these
     * two bars, so instead of a copy and paste deal, they're just dynamically
     * loaded in on the client side. */
    $('#navbar-wrapper').load('/static/common/navbar.html', function () {
        $('#sidebar-wrapper').load('/static/common/sidebar.html', function () {

            /* Expand and collapse the sidebar. */ 
            function toggle_sidebar() {
                $("#wrapper").toggleClass("toggled-2");
                if ($("#wrapper").hasClass("toggled-2")) {
                    Cookies.set("sidebar", "collapsed");
                    $("#menu li ul").css("padding-left", 0);
                } else {
                    Cookies.set("sidebar", "expanded");
                    $("#menu li ul").css("padding-left", 40);
                }
                //Collapse pills when sidebar changes
                //$('#menu ul').hide();
            }
            
            $('#menu ul').hide();
            $('#menu ul').children('.current').parent().show();
            //$('#menu ul:first').show();

            $("#menu-toggle").click(function (e) {
                e.preventDefault();
                $("#wrapper").toggleClass("toggled");
            });
            $("#menu-toggle-2").click(function (e) {
                e.preventDefault();
                toggle_sidebar();
            });
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
            if (Cookies.get("sidebar") === "collapsed") {
                toggle_sidebar();
            }
        });
    });
});
