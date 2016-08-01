var layer_fields = {
    'Raw': ['load'],
    'UDP': ['sport', 'dport'],
    'IP': ['src', 'dst', 'ttl'],
    'Ether': ['src', 'dst'],
    'Test': ['a','b','c','d','e','f'],
};

$(document).ready(function () {
    'use strict';

    var incID = 0;

    function getID() {
        return incID++;
    }

    function update_textbox_inputs(layer) {
        $("#field-inputs").html("");
        layer_fields[layer].forEach(function (field) {
            var label = $("<span/>", {
                class: "input-group-addon",
                html: field,
            });
            var input = $("<input/>", {
                type: "text",
                class: "form-control",
            });
            var temp = $("<div/>", {
                class: "input-group",
                html: label.add(input),
            });
            $("#field-inputs").append(temp);
        });
    }

    function update_selected_layers(layers) {
        $("#selected-layers").html("");
        layers.forEach(function (layer) {
            var temp = $("<button/>", {
                class: "btn btn-default packet-layer-selected",
                html: layer[0],
            });
            $("#selected-layers").prepend(temp);
        });

        $(".packet-layer-selected").click(function () {
            update_textbox_inputs($(this).html());
        });
    }

    var layers = [];

    $(".packet-layer-select").click(function () {
        var layer = $(this).children("a").text();
        var fields = [layer].concat(layer_fields[layer]);
        layers.push(fields);
        update_selected_layers(layers);
    });
});
