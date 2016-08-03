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

    function byte_array_to_long(/*byte[]*/byteArray) {
        var value = 0;
        for (var i = 0; i < byteArray.length; ++i) {
            value = (value * 256) + byteArray[i];
        }
        return value;
    };

    function string_to_byte_array(data) {
        var byteArray = data;
        var bytes = [];
        for (var i = 0; i < byteArray.length; ++i) {
            bytes = bytes.concat([byteArray.charCodeAt(i)]);
        }
        return bytes;
    }

    function unpack(str) {
        var bytes = [];
        for(var i = 0, n = str.length; i < n; i++) {
            var char = str.charCodeAt(i);
            bytes.push(char >>> 8, char & 0xFF);
        }
        return bytes;
    }

    function replaceAll(str, find, replace) {
        return str.replace(new RegExp(find, 'g'), replace);
    }

    function update_bar() {
        $.ajax({
            type: "POST",
            url: "command_and_respond?command=7;size=Q;;",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                console.log(data);
                var band = $("#bandwidth-bar");
                var max = parseInt(band.attr("aria-valuemax"));
                var bandwidth = byte_array_to_long(string_to_byte_array(data));
                console.log(bandwidth);
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
            url: "command?command=1;data=None;",
        });
    });

    $("#stop-sending").click(function () {
        $.ajax({
            type: "POST",
            url: "command?command=2;data=None;",
        });
    });

    $("#send-single").click(function () {
        $.ajax({
            type: "POST",
            url: "command?command=5;data=None;",
        });
    });
    
    setInterval(function () {
        update_bar();
    }, 1000);
});
