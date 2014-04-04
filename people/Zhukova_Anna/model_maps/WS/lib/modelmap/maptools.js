/**
 * Created by anna on 12/12/13.
 */

function adjustMapSize() {
    var dimention = Math.min($(window).height(), $(window).width());//screen.height, screen.width);
    var size = Math.max(256, Math.pow(2, Math.floor(Math.log(dimention) / Math.log(2))));
    var $map_div = $("#map");
    var old_width = $map_div.height();
    if (old_width != size) {
        $map_div.css({
            'height': size,
            'width': size
        });
        $(".leaflet-popup").css({
            "maxWidth": size,
            'maxHeight': size
        });
        $(".leaflet-popup-content").css({
            "maxWidth": size - 10,
            'maxHeight': size - 10
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


function uproject(map, x, y, w, h) {
    var r_x = map.unproject([x - w / 2, y], 1).distanceTo(map.unproject([x + w / 2, y], 1)),
        r_y = map.unproject([x, y + h / 2], 1).distanceTo(map.unproject([x, y - h / 2], 1));
    return (r_x + r_y) / 2;
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

function pnt2layer(map, feature, edges, ub_sps) {
    var e = feature.geometry.coordinates;
    var w = feature.properties.width / 2;
    var h = feature.properties.height / 2;
    if (EDGE == feature.properties.type) {
        var color = feature.properties.ubiquitous ? GREY : (feature.properties.generalized ? (feature.properties.transport ? TURQUOISE : GREEN) : (feature.properties.transport ? VIOLET : BLUE));
        var edge = L.polyline(e.map(function (coord) {
            return map.unproject(coord, 1)
        }), {
            color: color,//feature.properties.color,
            opacity: 1,
            weight: w * Math.pow(2, map.getZoom() - 1),
            lineCap: 'round',
            lineJoin: 'round',
            clickable: false,
            fill: false
        });
        if (feature.properties.ubiquitous) {
            ub_sps.addLayer(edge);
        }
        edges.addLayer(edge);
        return edges;
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
//    var centre = map.unproject(e, 1);
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
                    html: feature.properties.label,//formatLabel(feature, w * map.getZoom() * 2, h * map.getZoom() * 2),
                    iconSize: [  (w * Math.pow(2, map.getZoom() - 1) * 1.8), h * Math.pow(2, map.getZoom() - 1) * 1.8]
                })
            }
        );
        var fg = L.featureGroup([node, label]);
        if (feature.properties.ubiquitous) {
            ub_sps.addLayer(fg);
            // return ub_sps;
        }
        return fg;
    }
    if (feature.properties.ubiquitous) {
        ub_sps.addLayer(node);
        // return ub_sps;
    }
    return node;
}

function getGeoJson(map, json, name2popup) {
    var edges = L.layerGroup([]);
    var ub_sps = L.layerGroup([]);
    if (json == null || json.length == 0) {
        // pass
    } else if (json.length == 1) {
        getSimpleJson(map, json[0], name2popup, edges, ub_sps);
    } else {
        getComplexJson(map, json[0], json[1], name2popup, edges, ub_sps);
    }
    fitSimpleLabels();
    setAutocomplete(map, name2popup);
    return ub_sps;
}

function resizeEdges(edges, resize_factor, ub_sps, map) {
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
    var layers = edges.getLayers();
    for (var i in layers) {
        var e = layers[i];
        edges.removeLayer(e);
        props['color'] = e.options['color'];
        props['weight'] = e.options['weight'] * resize_factor;
        var new_e = L.polyline(e._latlngs, props);
        edges.addLayer(new_e);
        new_e.bringToBack();
        if (-1 != ub_sps.getLayers().indexOf(e)) {
            ub_sps.removeLayer(e);
            ub_sps.addLayer(new_e);
            if (!document.getElementById('showUbs').checked) {
                map.removeLayer(new_e);
            }
        }
    }
}

function getComplexJson(map, json_zo, json_zi, name2popup, edges, ub_sps) {
    var geojsonLayer = getSimpleJson(map, json_zo, name2popup, edges, ub_sps);
    var zo = map.getZoom();
    map.on('zoomend', function (e) {
        var zn = map.getZoom();
        if (zn >= 3 && zo < 3) {
            geojsonLayer = getJson(map, json_zi, name2popup, geojsonLayer, edges, ub_sps);
            fitSimpleLabels();
            setAutocomplete(map, name2popup);
        } else if (zn < 3 && zo >= 3) {
            geojsonLayer = getJson(map, json_zo, name2popup, geojsonLayer, edges, ub_sps);
            fitSimpleLabels();
            setAutocomplete(map, name2popup);
        } else {
            fitLabels(zn, zo);
            resizeEdges(edges, Math.pow(2, zn - zo), ub_sps, map);
        }
        zo = map.getZoom();
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

function getSimpleJson(map, jsn, name2popup, edges, ub_sps) {
    var result = L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, edges, ub_sps);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, feature, layer);
        }
    }).addTo(map);
    visualizeUbiquitous(map, ub_sps);
    return result;
}

function getJson(map, jsn, name2popup, geojsonLayer, edges, ub_sps) {
    for (var prop in name2popup) {
        if (name2popup.hasOwnProperty(prop)) {
            delete name2popup[prop];
        }
    }
    edges.clearLayers();
    ub_sps.clearLayers();
    map.removeLayer(geojsonLayer);
    return getSimpleJson(map, jsn, name2popup, edges, ub_sps);
}

function search(map, name2popup) {
    var srch = document.search_form.search_input.value;
    if (srch && name2popup[srch]) {
        name2popup[srch].openOn(map);
    }
}

function visualizeUbiquitous(map, ub_sps) {
    if (document.getElementById('showUbs').checked) {
        map.addLayer(ub_sps);
    } else {
        map.removeLayer(ub_sps);
        var layers = ub_sps.getLayers();
        for (var i in layers) {
            var e = layers[i];
            map.removeLayer(e);
        }
    }
}

function gup(name) {
    name = new RegExp('[?&]' + name.replace(/([[\]])/, '\\$1') + '=([^&#]*)');
    return (window.location.href.match(name) || ['', ''])[1];
}

function centerMap() {
    map.setView([0, 0], map.getZoom());
}