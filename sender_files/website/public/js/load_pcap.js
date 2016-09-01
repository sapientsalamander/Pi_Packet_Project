$(document).ready(function () {
    'use strict';

    $("#load-file-from-server").click(function () {
        $.ajax({
            type: "POST",
            url: "load_pcap_file?filename=" + $("#pcap_files option:selected").text(),
        });
   });

    $("#load-file-from-user").click(function () {
        $.ajax({
            type: "POST",
            url: "upload_pcap_file?" + //TODO:,
            success: function (data) {
                var filenames = JSON.parse(data);
                filenames.forEach(function (filename) {
                    var option = $("<option/>", {
                        html: filename,
                    });
                    $("#pcap_files").append(option);
                });
            },
            failure: function (errMsg) {
                alert(errMsg);
            }
        });
    });

    $.ajax({
        type: "POST",
        url: "get_pcap_filenames",
        success: function (data) {
            var filenames = JSON.parse(data);
            filenames.forEach(function (filename) {
                var option = $("<option/>", {
                    html: filename,
                });
                $("#pcap_files").append(option);
            });
        },
        failure: function (errMsg) {
            alert(errMsg);
        }
    });

});
