$(document).ready(function () {
    'use strict';

    var MAX_LINE_RATE = 100000000; // In bits / second. 100 Mbps
    var packet_size = 0;

    function byte_array_to_long(/*byte[]*/byteArray) {
        var value = 0;
        for ( var i = byteArray.length - 1; i >= 0; i--) {
            value = (value * 256) + byteArray[i] * 1;
        }
        return value;
    }

    function string_to_byte_array(data) {
        var byteArray = data;
        var bytes = [];
        for (var i = 0; i < byteArray.length; ++i) {
            bytes = bytes.concat([byteArray.charCodeAt(i)]);
        }
        return bytes;
    }

    function calculate_bandwidth(band) {
        var units = ["bps", "Kbps", "Mbps", "Gbps"];
        var i = 0;
        while (band >= 1000) {
            band /= 1000;
            i++;
        }
        return String(band.toFixed(2)) + " " + units[i];
    }
    
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
    
    function update_bar() {
        var band = $("#bandwidth-bar");
        var max = parseInt(band.attr("aria-valuemax"));
        var bandwidth = 8 * packet_size * $("#pps").val();
        band.css("width", String(bandwidth / MAX_LINE_RATE * 100) + "%");
        band.html(calculate_bandwidth(bandwidth));
    }

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
        // Doesn't work with IE
        //return [seconds].concat(Array.from(new Uint8Array(Uint32Array.valueOf(sleep_time).buffer)));
    }

    $("#done-configuration").click(function () {
        $.ajax({
            type: "POST",
            url: "command?command=3;data=" + pps_to_sleep(parseInt($("#pps").val())),
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

    $.ajax({
        type: "POST",
        url: "command_and_respond?command=8;data=None",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            packet_size = byte_array_to_long(string_to_byte_array(data));
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
