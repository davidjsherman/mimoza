/**
 * Created by anna on 12/12/13.
 */

function adjustMapSize() {
    const VIEWPORT_MARGIN = 50;
    const MIN_DIMENTION_SIZE = 256;
    var width = Math.max(MIN_DIMENTION_SIZE, $(window).width() - VIEWPORT_MARGIN);
    var height = Math.max(MIN_DIMENTION_SIZE, $(window).height() - VIEWPORT_MARGIN);
    var $map_div = $("#map");
    var old_height = $map_div.height();
    var old_width = $map_div.width();
    if (old_width != width || old_height != height) {
        $map_div.css({
            'height': height,
            'width': width
        });
        $(".leaflet-popup").css({
            'maxHeight': height,
            'maxWidth': width
        });
        const LEAFLET_POPUP_MARGIN = 10;
        $(".leaflet-popup-content").css({
            'maxHeight': height - LEAFLET_POPUP_MARGIN,
            'maxWidth': width -LEAFLET_POPUP_MARGIN
        });
    }
}

const MARGIN = 156;
const MAX_ZOOM = 5;
const MAP_DIMENSION_SIZE = 512;

const ZOOM_IN = 2;
const ZOOM_OUT = 1;
const ZOOM_ANY = 3;

function getBaseMap(layers) {
    adjustMapSize();

    var map = L.map('map', {
        maxZoom: MAX_ZOOM,
        minZoom: 0,
        attributionControl: false,
        padding: [MARGIN, MARGIN],
        layers: layers
    });

    var southWest = map.unproject([0 - MARGIN, MAP_DIMENSION_SIZE + MARGIN], 1);
    var northEast = map.unproject([MAP_DIMENSION_SIZE + MARGIN, 0 - MARGIN], 1);
    var bounds = new L.LatLngBounds(southWest, northEast);
    map.setView(bounds.getCenter(), 1);
    map.setMaxBounds(bounds);
    var popup = null;
    map.on('popupopen', function (e) {
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

function getTiles(img) {
    return L.tileLayer(img, {
        continuousWorld: true,
        noWrap: true,
        tileSize: 512,
        maxZoom: 5,
        minZoom: 0,
        tms: true,
        updateWhenIdle: true,
        reuseTiles: true
    });
}

function initializeMap(json_data) {
    var labels = L.layerGroup();

    var ubLayer = L.layerGroup();
    var tiles = getTiles("/lib/modelmap/white512.jpg");
    var gray_tiles =  getTiles("/lib/modelmap/gray512.jpg");
    var map = getBaseMap([tiles, ubLayer, labels]);

    var name2popup = {};

    if (json_data != null) {
        var any_ubiquitous = L.featureGroup();
        var any_ub_edges = L.layerGroup();
        any_ubiquitous.addTo(ubLayer);
        any_ub_edges.addTo(ubLayer);
        var any_edges = L.layerGroup();
        getSimpleJson(map, json_data, name2popup, any_edges, any_ub_edges, any_ubiquitous, labels, ZOOM_ANY).addTo(map);

        var zi_ubiquitous = L.featureGroup();
        var zi_ub_edges = L.layerGroup();
        var zi_edges = L.layerGroup();
        var zoom_in = getSimpleJson(map, json_data, name2popup, zi_edges, zi_ub_edges, zi_ubiquitous, labels, ZOOM_IN);

        var zo_ubiquitous = L.featureGroup();
        var zo_ub_edges = L.layerGroup();
        var zo_edges = L.layerGroup();
        zo_ub_edges.addTo(ubLayer);
        zo_ubiquitous.addTo(ubLayer);
        var zoom_out = getSimpleJson(map, json_data, name2popup, zo_edges, zo_ub_edges, zo_ubiquitous, labels, ZOOM_OUT);
        zoom_out.addTo(map);

        var zo = map.getZoom();
        map.on('zoomend', function (e) {
            var zn = map.getZoom();
            if (zn >= 3 && zo < 3) {
                ubLayer.removeLayer(zo_ub_edges);
                ubLayer.removeLayer(zo_ubiquitous);
                map.removeLayer(zoom_out);

                zi_ub_edges.addTo(ubLayer);
                zi_ubiquitous.addTo(ubLayer);
                map.addLayer(zoom_in);

                if (!map.hasLayer(ubLayer)) {
                    map.removeLayer(zi_ub_edges);
                    map.removeLayer(zi_ubiquitous);
                }
//                getJson(map, zoom_in, name2popup, geojsonLayer, edges, ub_edges, ubiquitous, labels);
            } else if (zn < 3 && zo >= 3) {
                ubLayer.removeLayer(zi_ub_edges);
                ubLayer.removeLayer(zi_ubiquitous);
                map.removeLayer(zoom_in);

                zo_ub_edges.addTo(ubLayer);
                zo_ubiquitous.addTo(ubLayer);
                map.addLayer(zoom_out);

                if (!map.hasLayer(ubLayer)) {
                    map.removeLayer(zo_ub_edges);
                    map.removeLayer(zo_ubiquitous);
                }
//                getJson(map, zoom_out, name2popup, geojsonLayer, edges, ub_edges, ubiquitous, labels);
//            } else {
//                fitLabels(zn, zo);
//                resizeEdges(edges, ub_edges, Math.pow(2, zn - zo), map);
            }
            zo = map.getZoom();
        });
    }
    fitSimpleLabels();
    setAutocomplete(map, name2popup);

    var baseLayers = {
        "White background": tiles,
        "Gray background": gray_tiles
    };

    var overlays = {
        "Ubiquitous species": ubLayer,
        "Labels": labels
    };

    L.control.layers(baseLayers, overlays).addTo(map);

    return map;
}

const EDGE = 0;

const SPECIES = 1;
const COMPARTMENT = 3;
const REACTION = 2;

const BG_SPECIES = 4;
const BG_REACTION = 5;
const BG_COMPARTMENT = 6;
const BG = [BG_SPECIES, BG_REACTION, BG_COMPARTMENT];

const GREY = "#B4B4B4";
const ORANGE = "#FDB462";
const YELLOW = "#FFFFB3";
const RED = "#FB8072";
const BLUE = "#80B1D3";
const GREEN = "#B3DE69";
const VIOLET = "#BEBADA";
const TURQUOISE = "#8DD3C7";
const WHITE = 'white';

const ROUND = 'round';

function pnt2layer(map, feature, edges, ub_edges, ubiquitous, labels) {
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
            lineCap: ROUND,
            lineJoin: ROUND,
            clickable: false,
            fill: false
        });
        return feature.properties.ubiquitous ? ub_edges.addLayer(edge) : edges.addLayer(edge);
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
        color: WHITE,
        fillOpacity: is_bg ? 0.3 : 1,
        opacity: 1,
        lineCap: ROUND,
        lineJoin: ROUND,
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
        return L.rectangle(bounds, props);
    }
    if (BG_COMPARTMENT == feature.properties.type) {
        props["fillColor"] = YELLOW;
        return L.rectangle(bounds, props);
    }
    var node = null;
    if (REACTION == feature.properties.type) {
        props["fillColor"] = feature.properties.generalized ? (feature.properties.transport ? TURQUOISE : GREEN) : (feature.properties.transport ? VIOLET : BLUE);
        node = L.rectangle(bounds, props);
    } else if (COMPARTMENT == feature.properties.type) {
        props["fillColor"] = YELLOW;
        node = L.rectangle(bounds, props);
    } else if (SPECIES == feature.properties.type) {
        props["fillColor"] = feature.properties.ubiquitous ? GREY : (feature.properties.generalized ? ORANGE : RED);
        node = L.circle(centre, d / 2, props);
    } else {
        return null;
    }
    if (!feature.properties.ubiquitous && w * Math.pow(2, (map.getZoom() >= 3 ? map.getMaxZoom() : 3) - 1) >= 25) {
        var label = L.marker(centre,
            {
                icon: L.divIcon({
                    className: 'count-icon',
                    html: feature.properties.label,
                    iconSize: [  (w * Math.pow(2, map.getZoom() - 1) * 1.8), h * Math.pow(2, map.getZoom() - 1) * 1.8]
                })
            }
        );
        labels.addLayer(label);
    }
    return feature.properties.ubiquitous ? ubiquitous.addLayer(node) : node;
}

function resizeEdges(edges, ub_edges, resize_factor, map) {
    if (1 == resize_factor) {
        return
    }
    var props = {
        opacity: 1,
        lineCap: ROUND,
        lineJoin: ROUND,
        clickable: false,
        fill: false
    };

    function resize(edgs) {
        var new_layers = [];
        edgs.eachLayer(function (e) {
            props['color'] = e.options['color'];
            props['weight'] = e.options['weight'] * resize_factor;
            var new_e = L.polyline(e._latlngs, props);
            new_layers.push(new_e);
        });
        edgs.clearLayers();
        new_layers.forEach(function (newLayer) {
            edgs.addLayer(newLayer);
        });
    }
    resize(ub_edges);
    resize(edges, true);
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
        console.log(e.keyCode);
        var code = (e.keyCode ? e.keyCode : e.which);
        if (code == $.ui.keyCode.ENTER) {
            search(map, name2popup);
            e.preventDefault();
        }
    });
    document.getElementById('search_form').onclick = function() {
        search(map, name2popup);
    };
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

function getSimpleJson(map, jsn, name2popup, edges, ub_edges, ubiquitous, labels, level) {
    return L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, edges, ub_edges, ubiquitous, labels);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, feature, layer);
        },
        filter: function (feature, layer) {
            var zoom = feature.properties.zoom;
            return level == zoom;
        }
    })
}

function clear(dict) {
    for (var prop in dict) {
        if (dict.hasOwnProperty(prop)) {
            delete dict[prop];
        }
    }
}

function getJson(map, jsn, name2popup, geojsonLayer, edges, ub_edges, ubiquitous, labels) {
    clear(name2popup);
    var showUbiquitous = map.hasLayer(ubiquitous);
    edges.clearLayers();
    ubiquitous.clearLayers();
    ub_edges.clearLayers();
    labels.clearLayers();
    geojsonLayer.addData(jsn);
    if (!showUbiquitous) {
        map.removeLayer(ubiquitous);
        map.removeLayer(ub_edges);
    }
    fitSimpleLabels();
    setAutocomplete(map, name2popup);
}

function gup(name) {
    name = new RegExp('[?&]' + name.replace(/([[\]])/, '\\$1') + '=([^&#]*)');
    return (window.location.href.match(name) || ['', ''])[1];
}

function centerMap() {
    map.setView([0, 0], map.getZoom());
}