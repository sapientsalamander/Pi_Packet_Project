$(document).ready(function () {
    'use strict';

    var MAX_LINE_RATE = 100000000; // In bits / second. 100 Mbps
    var packet_size = 0;

    /* Takes in a bandwidth in bits per second, and then simplifies the units,
     * and returns a string with the calculated value. */
    function calculate_bandwidth(band) {
        var units = ["bps", "Kbps", "Mbps", "Gbps"];
        var i = 0;
        while (band >= 1000) {
            band /= 1000;
            i++;
        }
        return String(band.toFixed(2)) + " " + units[i];
    }

    /* The pps bar only allows you to go up to 100 Mbps. However, the maximum
     * number of pps that you can send depends on the size of the packet.
     * When you get the current packet size, you call this, so then it
     * calculates the maximum number of pps that you can send. */    
    function update_max() {
        if (packet_size == 0) {
            $("#pps").attr("max", MAX_LINE_RATE);
        } else {
            var max = Math.floor(MAX_LINE_RATE / (packet_size * 8));
            $("#pps").attr("max", String(max));
        }
        $("#packet_size_text").html("with " + String(packet_size) + " byte packets");
        $("#pps").val("0");
    }

    /* Updates the pps bar. */
    function update_bar() {
        var band = $("#bandwidth-bar");
        var max = parseInt(band.attr("aria-valuemax"));
        var bandwidth = 8 * packet_size * $("#pps").val();
        band.css("width", String(bandwidth / MAX_LINE_RATE * 100) + "%");
        band.html(calculate_bandwidth(bandwidth));
    }

    /* Takes in a pps argument, then calculates the sleep time in between each
     * send packet to get to this target pps. The sleep time is calculated as
     * one byte for the seconds, then 4 more for the microseconds. */
    function pps_to_sleep(pps) {
        if (pps == 0) {
            return [0,0,0,0,0];
        }
        var SECOND_TO_MICROSECONDS = 1000000;
        var sleep_time = (1 * SECOND_TO_MICROSECONDS) / pps; 
        var seconds = 0;
        while (sleep_time >= SECOND_TO_MICROSECONDS) {
            sleep_time -= SECOND_TO_MICROSECONDS;
            seconds++;
        }
        var temp_buffer = new ArrayBuffer(4);
        var temp_32 = new Uint32Array(temp_buffer);
        var temp_8 = new Uint8Array(temp_buffer);
        temp_32[0] = sleep_time;
        return [seconds].concat([].slice.call(temp_8));
    }

    /* Done configuring the pps, send it to the C side. */
    $("#done-configuration").click(function () {
        $.ajax({
            type: "POST",
            url: "command?command=3&data=" + pps_to_sleep(parseInt($("#pps").val())),
            contentType: "application/json; charset=utf-8",
            success: function (data) {
            },
            failure: function (errMsg) {
                alert(errMsg);
            }
        });
    });

    $("#pps").change(function () {
        update_bar();
    });

    /* Request the size of the packet that is currently loaded in C memory. */
    $.ajax({
        type: "POST",
        url: "command_and_respond?command=8&size=I",
        contentType: "application/json; charset=utf-8",
        contentType: false,
        success: function (data) {
            packet_size = parseInt(data, 16);
            update_max();
            update_bar();    
            if (packet_size == 0) {
                $("#no-packet-warning").toggleClass("hidden");
            }
        },
        failure: function (errMsg) {
            alert(errMsg);
        }
    });

    // When you press enter, it refreshes the page. This disables that.
    $("form").submit(function () {
        return false;
    });
});
