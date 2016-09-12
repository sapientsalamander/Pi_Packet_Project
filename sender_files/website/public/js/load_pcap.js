$(document).ready(function () {
    'use strict';

    /* Load a file from the server files stored in pcap_files. */
    $("#load-file-from-server").click(function () {
        $.ajax({
            type: "POST",
            url: "load_pcap_file?filename=" + $("#pcap_files option:selected").text(),
        });
   });

    /* Takes the pcap file uploaded to input_file, and then sends it to the
     * server for processing. */
    $("#load-file-from-user").click(function () {
        var file = $("#input_file")[0].files[0];
        var form_data = new FormData();
        form_data.append("file_data", file);
        var request = new XMLHttpRequest();
        request.open("POST", "upload_pcap_file");
        request.send(form_data);
    });

    /* Get a list of filenames that are located in pcap_files, and then
     * appends each name to the input box for selection. */
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
