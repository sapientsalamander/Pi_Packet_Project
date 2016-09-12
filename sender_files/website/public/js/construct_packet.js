$(document).ready(function () {
    'use strict';

    var layer_fields = {};

    /* Used to remember which field is actively being configured, used for
     * removing a layer, updating the appropriate fields, etc. */
    var active_layer = undefined
    var active_layer_index = undefined;
    var incID = 0;
    var layers = [];

    function getID() {
        return incID++;
    }

    /* Get a list of layers and their fields, and then update layers with
     * that information. */
    $.ajax({
        type: "POST",
        url: "get_configurable_layers",
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            layer_fields = data;

            Object.keys(layer_fields).sort().forEach(function (layer) {
                var text = $("<a/>", {
                    href: "#",
                    html: layer,
                });
                var element = $("<li/>", {
                    class: "packet-layer-select",
                    html: text,
                });
                $("#layers-list").append(element);
            });

            /* Every time a layer is clicked (IP, Ether, etc.), update the
             * fields input with the appropriate fields (src, ttl, etc.)*/
            $(".packet-layer-select").click(function () {
                var layer = $(this).children("a").text();
                var temp_dict = {};
                temp_dict["layer_type"] = layer;
                temp_dict["li_id"] = getID();
                Object.keys(layer_fields[layer]).forEach(function (key) {
                    temp_dict[key] = layer_fields[layer][key];
                });
                layers.push(temp_dict);
                update_selected_layers(layers);
            });

        },
        failure: function (errMsg) {
            alert(errMsg);
        }
    });


    /* Called every time the selected layer changes, so we have to
     * update the text inputs to reflect the actual fields in a
     * certain layer */
    function update_textbox_inputs(layer) {
        $("#field-inputs").html("");

        /* Makes a new input group for each field. */
        Object.keys(layer_fields[layer]).forEach(function (key) {
            var label = $("<span/>", {
                class: "input-group-addon",
                html: key,
            });
            var input = $("<input/>", {
                type: "text",
                class: "form-control field-input",
                value: active_layer_index[key],
            }).attr("data-field-type", key);
            var temp = $("<div/>", {
                class: "input-group",
                html: label.add(input),
            });
            $("#field-inputs").append(temp);
        });

        /* Whenever you type in one of the input boxes, update
         * layers to reflect the added text. */
        $(".field-input").on("input", function () {
            active_layer_index[$(this).attr("data-field-type")] = this.value;
        });
    }

    /* Every time you add a layer, the entire list of selected layers
     * is cleared out, and then readded, with the new one prepended to
     * the beginning. */
    function update_selected_layers(layers) {
        $("#selected-layers").html("");

        layers.forEach(function (layer) {
            var temp = $("<button/>", {
                class: "btn btn-default packet-layer-selected",
                html: layer["layer_type"],
                id: layer["li_id"],
            });
            $("#selected-layers").prepend(temp);
        });
        $(".packet-layer-selected").click(function () {
            if (this.id !== active_layer) {
                $("#" + active_layer).css("background-color", "transparent");
                active_layer = this.id;

                /* Used for determining which index in the layers list is
                 * tied to the active layer. */
                active_layer_index = layers.filter(function (val) {
                    return String(val["li_id"]) === active_layer;
                })[0];

                update_textbox_inputs($(this).html());
                $(this).css("background-color", "#ccc");
            } else {
                active_layer = undefined;
                active_layer_index = undefined;
                $(this).css("background-color", "transparent");
                $("#field-inputs").html("");
            }
        });
        $("#" + active_layer).css("background-color", "#ccc");
    }

    /* Delete the active layer. */
    $("#delete-button").click(function () {
        if (active_layer >= 0) {
            layers.splice(layers.indexOf(active_layer_index), 1);
            active_layer = undefined;
            active_layer_index = undefined;
            $("#field-inputs").html("");
            update_selected_layers(layers);
        }
    });

    /* Move the active layer down in the list. */    
    $("#down-button").click(function () {
        var index = layers.indexOf(active_layer_index);
        if (active_layer >= 0 && index !== 0) {
            layers[index - 1] = layers.splice(index, 1, layers[index - 1])[0];
            update_selected_layers(layers);
        }
    });

    /* Move the active layer up in the list. */
    $("#up-button").click(function () {
        var index = layers.indexOf(active_layer_index);
        if (active_layer >= 0 && index !== layers.length - 1) {
            layers[index] = layers.splice(index + 1, 1, layers[index])[0];
            update_selected_layers(layers);
        }
    });

    /* Send the configured packet to the C side. */
    $("#done-configuration").click(function() {
        var req = "";
        console.log(JSON.stringify(layers));
        /* More efficient deep copy. */
        var layers_temp = JSON.parse(JSON.stringify(layers));

        layers_temp.forEach(function (entry) {
            delete entry["li_id"];
        });

        $.ajax({
            type: "POST",
            url: "packet_config?packet_layers=" + JSON.stringify(layers_temp),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (data) {
                alert(data);
            },
            failure: function (errMsg) {
                alert(errMsg);
            }
        });
    });

    /* Save a pcap file on the server for later selection. */
    $("#save-file").click(function () {
        var layers_temp = JSON.parse(JSON.stringify(layers));

        layers_temp.forEach(function (entry) {
            delete entry["li_id"];
        });

        var filename = $("#filename").val();

         $.ajax({
            type: "POST",
            url: "save_packet_to_file?pcap_filename=" + filename + "&packet_layers=" + JSON.stringify(layers_temp),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (data) {
                alert(data);
            },
            failure: function (errMsg) {
                alert(errMsg);
            }
        });
    });

    /* Prompt the user to save a pcap file on their local computer. */
    $("#save-file-local").click(function () {
        var layers_temp = JSON.parse(JSON.stringify(layers));

        layers_temp.forEach(function (entry) {
            delete entry["li_id"];
        });

        var filename = $("#filename").val();

        var xhr = new XMLHttpRequest();
        xhr.open("POST", "return_pcap_file?packet_layers=" + JSON.stringify(layers_temp), true);
        xhr.responseType = "arraybuffer";
        xhr.setRequestHeader('Content-type', 'application/json; charset=utf-8');
        xhr.onload = function(e) {
            if (this.status == 200) {
                var blob = new Blob([this.response], {type: "text\/plain; charset=x-user-defined"});
                var downloadUrl = URL.createObjectURL(blob);
                var a = document.createElement("a");
                a.href = downloadUrl;
                a.download = filename + ".pcap";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }
        };
        xhr.send();
    });

});
