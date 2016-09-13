$(document).ready(function () {
    'use strict';

    var MAX_LINE_RATE = 100000000; // In bits / second. 100 Mbps

    function calculate_bandwidth(band) {
        var units = ["bps", "Kbps", "Mbps", "Gbps"];
        var i = 0;
        while (band >= 1000) {
            band /= 1000;
            i++;
        }
        return String(band.toFixed(2)) + " " + units[i];
    }

    /* Requests the bandwidth and updates the progress bar to represent
     * the current bandwidth. */
    function update_bar() {
        $.ajax({
            type: "POST",
            url: "command_and_respond?command=7&size=Q",
            success: function (data) {
                var band = $("#bandwidth-bar");
                var max = parseInt(band.attr("aria-valuemax"));
                var bandwidth = parseInt(data, 16);
                band.css("width", String(bandwidth / MAX_LINE_RATE * 100) + "%");
                band.html(calculate_bandwidth(bandwidth));
            },
            failure: function (errMsg) {
                alert(errMsg);
            }
        });
    }

    $("#start-sending").click(function () {
        $.ajax({
            type: "POST",
            url: "command?command=1&data=None",
            contentType: "application/json; charset=utf-8",
        });
    });

    $("#stop-sending").click(function () {
        $.ajax({
            type: "POST",
            url: "command?command=2;data=None;",
            contentType: "application/json; charset=utf-8",
        });
    });

    $("#send-single").click(function () {
        $.ajax({
            type: "POST",
            url: "command?command=5;data=None;",
            contentType: "application/json; charset=utf-8",
        });
    });

    /* Gets the bandwidth from C side once every second. */
    setInterval(function () {
        update_bar();
    }, 1000);
});
