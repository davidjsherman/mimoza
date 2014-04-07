/**
 * Created by anna on 12/12/13.
 */

function adjustMapSize() {
//    var dimention = Math.min($(window).height(), $(window).width());//screen.height, screen.width);
    var width = Math.max(256, Math.pow(2, Math.floor(Math.log($(window).width()) / Math.log(2))));
    var height = Math.max(256, Math.pow(2, Math.floor(Math.log($(window).height()) / Math.log(2))));
//    var size = Math.max(256, Math.pow(2, Math.floor(Math.log(dimention) / Math.log(2))));
    var $map_div = $("#map");
    var old_height = $map_div.height();
    var old_width = $map_div.width();
//    if (old_width != size) {
    if (old_width != width || old_height != height) {
        $map_div.css({
//            'height': size,
//            'width': size
            'height': height,
            'width': width
        });
        $(".leaflet-popup").css({
//            "maxWidth": size,
//            'maxHeight': size
            'maxHeight': height,
            'maxWidth': width
        });
        $(".leaflet-popup-content").css({
//            "maxWidth": size - 10,
//            'maxHeight': size - 10
            'maxHeight': height - 10,
            'maxWidth': width -10
        });
    }
}

function initializeMap(max_zoom) {
    adjustMapSize();
    var margin = 156;
    var map = L.map('map', {
        maxZoom: max_zoom,
        minZoom: 0,
        attributionControl: false,
        padding: [156, 156]
    });
    var southWest = map.unproject([0 - margin, 512 + margin], 1);
    var northEast = map.unproject([512 + margin, 0 - margin], 1);
    var bounds = new L.LatLngBounds(southWest, northEast);
    map.setView(bounds.getCenter(), 1);
    map.setMaxBounds(bounds);
    var popup = null;
    map.on('popupopen', function (e) {
        console.log(e.popup);
        popup = e.popup;
    });
    map.on('dragstart', function (e) {
        if (popup) {
            console.log(e);
            map.closePopup(popup);
            popup.options['keepInView'] = false;
            map.openPopup(popup);
            popup.options['keepInView'] = true;
            popup = null;
        }
    });

    window.onresize = function (event) {
        adjustMapSize();
    };

    return map;
}

var EDGE = 0;

var SPECIES = 1;
var COMPARTMENT = 3;
var REACTION = 2;

var BG_SPECIES = 4;
var BG_REACTION = 5;
var BG_COMPARTMENT = 6;
var BG = [BG_SPECIES, BG_REACTION, BG_COMPARTMENT];

var GREY = "#B4B4B4";
var ORANGE = "#FDB462";
var YELLOW = "#FFFFB3";
var RED = "#FB8072";
var BLUE = "#80B1D3";
var GREEN = "#B3DE69";
var VIOLET = "#BEBADA";
var TURQUOISE = "#8DD3C7";

function pnt2layer(map, feature, edges, ub_edges, ub_sps) {
    var e = feature.geometry.coordinates;
    var w = feature.properties.width / 2;
    var h = feature.properties.height / 2;
    if (EDGE == feature.properties.type) {
        var color = feature.properties.ubiquitous ? GREY : (feature.properties.generalized ? (feature.properties.transport ? TURQUOISE : GREEN) : (feature.properties.transport ? VIOLET : BLUE));
        var edge = L.polyline(e.map(function (coord) {
            return map.unproject(coord, 1)
        }), {
            color: color,
            opacity: 1,
            weight: w * Math.pow(2, map.getZoom() - 1),
            lineCap: 'round',
            lineJoin: 'round',
            clickable: false,
            fill: false
        });
        if (feature.properties.ubiquitous) {
            ub_edges.addLayer(edge);
            return ub_edges;
        } else {
            edges.addLayer(edge);
            return edges;
        }
    }
    var x = e[0], y = e[1];
    if ((SPECIES == feature.properties.type) || (BG_SPECIES == feature.properties.type)) {
        w /= Math.sqrt(2);
        h /= Math.sqrt(2);
    }
    var is_bg = -1 != BG.indexOf(feature.properties.type);
    var props = {
        name: feature.properties.name,
        title: feature.properties.name,
        alt: feature.properties.name,
        id: feature.properties.id,
        color: 'white', //feature.properties.border,
        //fillColor: feature.properties.color,
        fillOpacity: is_bg ? 0.3 : 1,
        opacity: 1,
        lineCap: 'round',
        lineJoin: 'round',
        weight: is_bg ? 0 : Math.min(2, w / 10 * Math.pow(2, map.getZoom() - 1)),
        fill: true,
        clickable: !is_bg
    };
    var southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1),
        bounds = new L.LatLngBounds(southWest, northEast);
    var d = southWest.distanceTo(northEast);
    var centre = bounds.getCenter();
    if (BG_SPECIES == feature.properties.type) {
        props["fillColor"] = ORANGE;
        return L.circle(centre, d / 1.8, props);
    }
    if (BG_REACTION == feature.properties.type) {
        props["fillColor"] = feature.properties.transport ? TURQUOISE : GREEN;
        return  L.rectangle(bounds, props);
    }
    if (BG_COMPARTMENT == feature.properties.type) {
        props["fillColor"] = YELLOW;
        return  L.rectangle(bounds, props);
    }
    var node = null;
    if (REACTION == feature.properties.type) {
        props["fillColor"] = feature.properties.generalized ? (feature.properties.transport ? TURQUOISE : GREEN) : (feature.properties.transport ? VIOLET : BLUE);
        node = L.rectangle(bounds, props);
    }
    if (COMPARTMENT == feature.properties.type) {
        props["fillColor"] = YELLOW;
        node = L.rectangle(bounds, props);
    }
    if (SPECIES == feature.properties.type) {
        props["fillColor"] = feature.properties.ubiquitous ? GREY : (feature.properties.generalized ? ORANGE : RED);
        node = L.circle(centre, d / 2, props);
    }
    if (node && w * Math.pow(2, (map.getZoom() >= 3 ? map.getMaxZoom() : 3) - 1) >= 25) {
        var label = L.marker(centre,
            {
                icon: L.divIcon({
                    className: 'count-icon',
                    html: feature.properties.label,
                    iconSize: [  (w * Math.pow(2, map.getZoom() - 1) * 1.8), h * Math.pow(2, map.getZoom() - 1) * 1.8]
                })
            }
        );
        var fg = L.featureGroup([node, label]);
        if (feature.properties.ubiquitous) {
            ub_sps.addLayer(fg);
        }
        return fg;
    }
    if (feature.properties.ubiquitous) {
        ub_sps.addLayer(node);
    }
    return node;
}

function getGeoJson(map, json, name2popup) {
    var edges = L.layerGroup([]);
    var ub_edges = L.layerGroup([]);
    var ub_sps = L.layerGroup([]);
    if (json != null && json.length >= 2) {
        var zoom_in = json[1];
        var zoom_out = json[0];
        var geojsonLayer = getSimpleJson(map, zoom_out, name2popup, edges, ub_edges, ub_sps);
        var zo = map.getZoom();
        map.on('zoomend', function (e) {
            var zn = map.getZoom();
            if (zn >= 3 && zo < 3) {
                geojsonLayer = getJson(map, zoom_in, name2popup, geojsonLayer, edges, ub_edges, ub_sps);
            } else if (zn < 3 && zo >= 3) {
                geojsonLayer = getJson(map, zoom_out, name2popup, geojsonLayer, edges, ub_edges, ub_sps);
            } else {
                fitLabels(zn, zo);
                resizeEdges(edges, ub_edges, Math.pow(2, zn - zo));
            }
            zo = map.getZoom();
        });
    }
    fitSimpleLabels();
    setAutocomplete(map, name2popup);

    var checkbox = document.getElementById('showUbs');
    if (checkbox) {
        checkbox.onchange = function () {
            visualizeUbiquitous(map, edges, ub_edges, ub_sps);
        }
    }
}

function resizeEdges(edges, ub_edges, resize_factor) {
    if (1 == resize_factor) {
        return
    }
    var props = {
        opacity: 1,
        lineCap: 'round',
        lineJoin: 'round',
        clickable: false,
        fill: false
    };
    var show_ubs = document.getElementById('showUbs').checked;

    function resize(edgs, show) {
        var new_layers = [];
        edgs.eachLayer(function (e) {
            props['color'] = e.options['color'];
            props['weight'] = e.options['weight'] * resize_factor;
            var new_e = L.polyline(e._latlngs, props);
            new_layers.push(new_e);
        });
        edgs.clearLayers();
        new_layers.forEach(function (newLayer, i, array) {
            edgs.addLayer(newLayer);
            if (show) {
                newLayer.bringToBack();
            }
        });
    }
    resize(ub_edges, show_ubs);
    resize(edges, true);
}

function bringToBack(layerGroup) {
    layerGroup.eachLayer(function (layer) {
        layer.bringToBack();
    });
}

function fitSimpleLabels() {
    // console.log('fitting labels into nodes');
    $('.count-icon', '#map').each(function (i, obj) {
        var width = $(this).width();
        var size = width < 8 ? 0 : Math.max(width / 5, 8);
        $(this).css({
            'font-size': size
        });
    });
}

function setAutocomplete(map, name2popup) {
    var availableTags = Object.keys(name2popup);
    $("#tags").autocomplete({
        source: availableTags
    });
    $('#tags').keypress(function (e) {
        if (e.keyCode == '13') {
            e.preventDefault();
            search(map, name2popup);
        }
    });
}

function fitLabels(zn, zo) {
//    console.log('fitting labels into nodes');
//    var pow = Math.pow(2, zn - zo);
//    var width2css = {};
//    $('.count-icon', '#map').each(function (i, obj) {
//        var old_width = $(this).width();
//        if (old_width in width2css) {
//            $(this).css(width2css[old_width]);
//        } else {
//            var width = old_width * pow;
//            var old_height = $(this).height();
//            var height = old_height * pow;
//            var size = width < 10 ? 0 : Math.max(width / 5, 8);
//            var css = {
//                'height': height,
//                'width': width,
//                'font-size': size
//                //'top': $(this).offset().top + (old_height - height) / 2
//            };
//            $(this).css(css);
//            width2css[old_width] = css;
//        }
//        var offset = $(this).offset();
//        var shift = old_width * (1 - pow) / 2;
//        $(this).offset({ top: offset.top + shift, left: offset.left + shift});//{ top: offset.top + (old_height - height) / 2, left: offset.left + (old_width - width) / 2});
////        if (width >= 12 && size > 6) {
////            $(this).wrapInner("<div class='wrap'></div>");
////            var $i = $(this).children('.wrap')[0];
////            while($i.scrollHeight > height && size > 6) {
////                size--;
////                $(this).css("font-size", size);
////            }
////        }
//    });
////    $('.wrap').children().unwrap();
}

function getSimpleJson(map, jsn, name2popup, edges, ub_edges, ub_sps) {
    var result = L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, edges, ub_edges, ub_sps);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, feature, layer);
        }
    }).addTo(map);
    visualizeUbiquitous(map, edges, ub_edges, ub_sps);
    return result;
}

function getJson(map, jsn, name2popup, geojsonLayer, edges, ub_edges, ub_sps) {
    for (var prop in name2popup) {
        if (name2popup.hasOwnProperty(prop)) {
            delete name2popup[prop];
        }
    }
    edges.clearLayers();
    ub_sps.clearLayers();
    ub_edges.clearLayers();
    map.removeLayer(geojsonLayer);
    var result = getSimpleJson(map, jsn, name2popup, edges, ub_edges, ub_sps);
    fitSimpleLabels();
    setAutocomplete(map, name2popup);
    return result;
}

function search(map, name2popup) {
    var srch = document.search_form.search_input.value;
    if (srch && name2popup[srch]) {
        name2popup[srch].openOn(map);
    }
}

function removeLayer(map, layer) {
    layer.eachLayer(function (e) {
        map.removeLayer(e);
    });
}

function addLayer(map, layer) {
    layer.eachLayer(function (e) {
        map.addLayer(e);
    });
}

function visualizeUbiquitous(map, edges, ub_edges, ub_sps) {
    var checkBox = document.getElementById('showUbs');
    if (checkBox != null && checkBox.checked) {
        addLayer(map, ub_sps);
        map.addLayer(ub_edges);
        bringToBack(ub_edges);
        bringToBack(edges);
    } else {
        removeLayer(map, ub_sps);
        map.removeLayer(ub_edges);
    }
}

function gup(name) {
    name = new RegExp('[?&]' + name.replace(/([[\]])/, '\\$1') + '=([^&#]*)');
    return (window.location.href.match(name) || ['', ''])[1];
}

function centerMap() {
    map.setView([0, 0], map.getZoom());
}