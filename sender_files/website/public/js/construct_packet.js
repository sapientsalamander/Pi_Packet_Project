var layer_fields = {
    'Raw': ['load'],
    'UDP': ['sport', 'dport'],
    'IP': ['src', 'dst', 'ttl'],
    'Ether': ['src', 'dst'],
    'Test': ['a', 'b', 'c', 'd', 'e', 'f'],
};

$(document).ready(function () {
    'use strict';

    var active_layer = undefined
    var active_layer_index = undefined;
    var incID = 0;
    var layers = [];

    function getID() {
        return incID++;
    }

    /* Called every time the selected layer changes, so we have to
     * update the text inputs to reflect the actual fields in a
     * certain layer */
    function update_textbox_inputs(layer) {
        $("#field-inputs").html("");

        /* Makes a new input group for each field. */
        layer_fields[layer].forEach(function (field) {
            var label = $("<span/>", {
                class: "input-group-addon",
                html: field,
            });
            var input = $("<input/>", {
                type: "text",
                class: "form-control field-input",
                value: active_layer_index[field],
            }).attr("data-field-type", field);
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
                html: layer["type"],
                id: layer["id"],
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
                    return String(val["id"]) === active_layer;
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

    $(".packet-layer-select").click(function () {
        var layer = $(this).children("a").text();
        var temp_dict = {};
        temp_dict["type"] = layer;
        temp_dict["id"] = getID();
        layer_fields[layer].forEach(function (field) {
            temp_dict[field] = "";
        });
        layers.push(temp_dict);
        update_selected_layers(layers);
    });

    $("#delete-button").click(function () {
        if (active_layer >= 0) {
            layers.splice(layers.indexOf(active_layer_index), 1);
            active_layer = undefined;
            active_layer_index = undefined;
            $("#field-inputs").html("");
            update_selected_layers(layers);
        }
    });
    
    $("#down-button").click(function () {
        var index = layers.indexOf(active_layer_index);
        if (active_layer >= 0 && index !== 0) {
            layers[index - 1] = layers.splice(index, 1, layers[index - 1])[0];
            update_selected_layers(layers);
        }
    });
    
    $("#up-button").click(function () {
        var index = layers.indexOf(active_layer_index);
        if (active_layer >= 0 && index !== layers.length - 1) {
            layers[index] = layers.splice(index + 1, 1, layers[index])[0];
            update_selected_layers(layers);
        }
    });
    
    $("#done-configuration").click(function() {
        var req = "";
        console.log(JSON.stringify(layers));
        
        $.ajax({
            type: "POST",
            url: "packet_config?packet=" + JSON.stringify(layers),
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

});
