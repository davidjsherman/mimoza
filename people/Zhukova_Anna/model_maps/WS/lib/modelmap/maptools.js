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
const ZOOM_CHANGING = 3;

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

function clearLabels(map, labels) {
    for (var z = map.getMinZoom(); z <= map.getMaxZoom(); z++) {
        if (map.getZoom() != z && labels.hasOwnProperty(z)) {
            labels[z].eachLayer(function(layer) {
                map.removeLayer(layer);
            });
        }
    }
}
function initializeMap(json_data) {
    var labels = {};
    var ub_labels = {};

    var ubLayer = L.layerGroup();
    var labelsLayer = L.featureGroup();
    var tiles = getTiles("lib/modelmap/white512.jpg");
    var gray_tiles =  getTiles("lib/modelmap/gray512.jpg");
    var map = getBaseMap([tiles, labelsLayer, ubLayer]);


    if (json_data == null) {
        return map;
    }
    var name2selection = {};

    var any_ubiquitous = L.featureGroup();
    var any_ub_edges = L.layerGroup();
    any_ubiquitous.addTo(ubLayer);
    any_ub_edges.addTo(ubLayer);
    var any_edges = L.layerGroup();
    var any_name2popup = {};
    var ub_names = {};
//    var zoom2json = {};
    for (var z = 0; z <= MAX_ZOOM; z++) {
        getGeoJson(map, json_data, z, ubLayer);
    }
//    zoom2json[0].addTo(map);
//    setAutocomplete(map, any_name2popup, null);


//    var zi_ubiquitous = L.featureGroup();
//    var zi_ub_edges = L.layerGroup();
//    var zi_edges = L.layerGroup();
//    var zi_name2popup = jQuery.extend({}, any_name2popup);
//    var zoom_in = getSimpleJson(map, json_data, zi_name2popup, ub_names, name2selection, zi_edges, zi_ub_edges, zi_ubiquitous, labels, ub_labels, ZOOM_IN, ZOOM_CHANGING, map.getMaxZoom());
//
//    var zo_ubiquitous = L.featureGroup();
//    var zo_ub_edges = L.layerGroup();
//    var zo_edges = L.layerGroup();
//    zo_ub_edges.addTo(ubLayer);
//    zo_ubiquitous.addTo(ubLayer);
//    var zo_name2popup = any_name2popup;
//    var zoom_out = getSimpleJson(map, json_data, zo_name2popup, ub_names, name2selection, zo_edges, zo_ub_edges, zo_ubiquitous, labels, ub_labels, ZOOM_OUT, map.getMinZoom(), ZOOM_CHANGING - 1);
//    zoom_out.addTo(map);

//    setAutocomplete(map, zo_name2popup, null);

//    var zo = map.getZoom();
//    [labels, ub_labels].forEach(function(ls) {
//        clearLabels(map, ls);
//        if (ls.hasOwnProperty(zo)) {
//            labelsLayer.addLayer(ls[zo]);
//        }
//    });
//    map.on('zoomstart', function (e) {
//        [labels, ub_labels].forEach(function(ls) {
//            clearLabels(map, ls);
//            if (ls.hasOwnProperty(zo)) {
//                labelsLayer.removeLayer(ls[zo]);
//            }
//        });
//    });
//    map.on('zoomend', function (e) {
//        var zn = map.getZoom();
//        map.removeLayer(zoom2json[zo]);
//        map.addLayer(zoom2json[zn]);

//        ubLayer.removeLayer(zi_ub_edges);
//        ubLayer.removeLayer(zi_ubiquitous);
//        map.removeLayer(zoom_in);
//
//        zo_ub_edges.addTo(ubLayer);
//        zo_ubiquitous.addTo(ubLayer);
//        map.addLayer(zoom_out);
//        [labels, ub_labels].forEach(function(ls) {
//            clearLabels(map, ls);
//        });
//        setAutocomplete(map, zo_name2popup, map.hasLayer(ubLayer) ? null : ub_names);
//
//        if (!map.hasLayer(ubLayer)) {
//            map.removeLayer(zo_ub_edges);
//            map.removeLayer(zo_ubiquitous);
//        }



//        if (zn >= ZOOM_CHANGING && zo < ZOOM_CHANGING) {
//            ubLayer.removeLayer(zo_ub_edges);
//            ubLayer.removeLayer(zo_ubiquitous);
//            map.removeLayer(zoom_out);
//
//            zi_ub_edges.addTo(ubLayer);
//            zi_ubiquitous.addTo(ubLayer);
//            map.addLayer(zoom_in);
//            [labels, ub_labels].forEach(function(ls) {
//                clearLabels(map, ls);
//            });
//            setAutocomplete(map, zi_name2popup, map.hasLayer(ubLayer) ? null : ub_names);
//
//            if (!map.hasLayer(ubLayer)) {
//                map.removeLayer(zi_ub_edges);
//                map.removeLayer(zi_ubiquitous);
//            }
//        } else if (zn < ZOOM_CHANGING && zo >= ZOOM_CHANGING) {
//            ubLayer.removeLayer(zi_ub_edges);
//            ubLayer.removeLayer(zi_ubiquitous);
//            map.removeLayer(zoom_in);
//
//            zo_ub_edges.addTo(ubLayer);
//            zo_ubiquitous.addTo(ubLayer);
//            map.addLayer(zoom_out);
//            [labels, ub_labels].forEach(function(ls) {
//                clearLabels(map, ls);
//            });
//            setAutocomplete(map, zo_name2popup, map.hasLayer(ubLayer) ? null : ub_names);
//
//            if (!map.hasLayer(ubLayer)) {
//                map.removeLayer(zo_ub_edges);
//                map.removeLayer(zo_ubiquitous);
//            }
//        }
//        if (labels.hasOwnProperty(zn)) {
//            labelsLayer.addLayer(labels[zn]);
//        }
//        if (ub_labels.hasOwnProperty(zn) && map.hasLayer(ubLayer)) {
//            labelsLayer.addLayer(ub_labels[zn]);
//        }
//        zo = zn;
//    });

    map.on('overlayadd', function(e) {
        if (e.layer == ubLayer) {
            setAutocomplete(map, map.getZoom() < ZOOM_CHANGING ? zo_name2popup : zi_name2popup, null);
        }
    });

    map.on('overlayremove', function(e) {
        if (e.layer == ubLayer) {
            clearLabels(map, labels);
            setAutocomplete(map, map.getZoom() < ZOOM_CHANGING ? zo_name2popup : zi_name2popup, ub_names);
        }
    });

    var baseLayers = {
        "White background": tiles,
        "Gray background": gray_tiles
    };

    var overlays = {
        "Ubiquitous species": ubLayer
//        "Labels": labelsLayer
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

function pnt2layer(map, feature, zoom) {
    var e = feature.geometry.coordinates;
    var w = feature.properties.width / 2;
    var h = feature.properties.height / 2;
    if (EDGE == feature.properties.type) {
        var color = feature.properties.ubiquitous ? GREY : (feature.properties.generalized ? (feature.properties.transport ? TURQUOISE : GREEN) : (feature.properties.transport ? VIOLET : BLUE));
        return L.polyline(e.map(function (coord) {
            return map.unproject(coord, 1)
        }), {
            color: color,
            opacity: 1,
            weight: w * Math.pow(2, zoom - 1),
            lineCap: ROUND,
            lineJoin: ROUND,
            clickable: false,
            fill: false,
            zIndexOffset: -2000,
            riseOnHover: false
        });
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
        clickable: !is_bg,
        zIndexOffset: is_bg ? -2000 : 1000,
        riseOnHover: !is_bg
    };
    var southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1),
        bounds = new L.LatLngBounds(southWest, northEast);
    var d = southWest.distanceTo(northEast);
    var centre = map.unproject([x, y], 1);//bounds.getCenter();
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
    node = L.featureGroup([node]);
    var scaleFactor = Math.pow(2, zoom);
    if (h * scaleFactor >= 10) {
        var size = Math.max(h * scaleFactor / 4, 8);
        var label = L.marker(centre,
            {
                icon: L.divIcon({
                    className: 'label',
                    html: "<span style=\"font-size:" + size + "px;line-height:" + (size + 4) + "px\">" + feature.properties.label + "</span>",
                    iconSize: [w * scaleFactor, h * scaleFactor],
                    zIndexOffset: -1000,
                    riseOnHover: false
                })
            }
        );
        node.addLayer(label);
    }
    return node;
}

function addLayer(map, key, value) {
    if (map.hasOwnProperty(key)) {
        map[key].addLayer(value);
    } else {
        map[key] = L.featureGroup([value]);
    }
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
    resize(edges);
}

function setAutocomplete(map, name2popup, banned) {
    const searchForm = document.getElementById('search_form');
    if (searchForm != null) {
        var availableTags = Object.keys(name2popup);
        var value = searchForm.search_input.value;
        if (banned != null) {
            availableTags = availableTags.filter(function (element) {
                return !banned.hasOwnProperty(element);
            });
            if (banned.hasOwnProperty(value)) {
                searchForm.search_input.value = '';
            }
        }
        if (!name2popup.hasOwnProperty(value)) {
            searchForm.search_input.value = '';
        }
        $("#tags").autocomplete({
            source: availableTags,
            autoFocus: true
        });
        $('#tags').keypress(function (e) {
            var code = (e.keyCode ? e.keyCode : e.which);
            if (code == $.ui.keyCode.ENTER) {
                search(map, name2popup);
                e.preventDefault();
            }
        });
        searchForm.onclick = function () {
            search(map, name2popup);
        };
    }
}

function getSimpleJson(map, jsn, name2popup, ub_names, name2selection, edges, ub_edges, ubiquitous, labels, ub_labels, level) {
    return L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, edges, ub_edges, ubiquitous, labels, ub_labels);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, ub_names, name2selection, feature, layer);
        },
        filter: function (feature, layer) {
            return matchesLevel(level, feature);
        }
    })
}

function getSpecificJson(map, jsn, name2popup, ub_names, name2selection, level) {
    return L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, level);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, ub_names, name2selection, feature, layer);
        },
        filter: function (feature, layer) {
            return !feature.properties.ubiquitous && matchesLevel(level, feature);
        }
    })
}

function getUbiquitousJson(map, jsn, name2popup, ub_names, name2selection, level) {
    return L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, level);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, ub_names, name2selection, feature, layer);
        },
        filter: function (feature, layer) {
            return feature.properties.ubiquitous && matchesLevel(level, feature);
        }
    })
}

function matchesLevel(level, feature) {
    return level >= feature.properties.zoom_min && level <= feature.properties.zoom_max
}

function getGeoJson(map, json_data, z, ubLayer) {
    var name2selection = {};
    var name2popup = {};
    var ub_names = {};

    var sp_json = getSpecificJson(map, json_data, name2popup, ub_names, name2selection, z);
    var ub_json = getUbiquitousJson(map, json_data, name2popup, ub_names, name2selection, z);
    ub_json.addTo(ubLayer);
    if (map.getZoom() == z) {
        sp_json.addTo(map);
        ub_json.addTo(map);
    }

//    setAutocomplete(map, name2popup, null);

    map.on('zoomend', function (e) {
        var zoom = map.getZoom();
        // if we are about to zoom in/out to this geojson
        if (zoom == z) {
            map.addLayer(sp_json);
            map.addLayer(ub_json);
        } else {
            if (map.hasLayer(sp_json)) {
                map.removeLayer(sp_json);
            }
            if (map.hasLayer(ub_json)) {
                map.removeLayer(ub_json);
            }
        }
    });
//    setAutocomplete(map, zo_name2popup, null);
}


function clear(dict) {
    for (var prop in dict) {
        if (dict.hasOwnProperty(prop)) {
            delete dict[prop];
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

function overlay() {
    el = document.getElementById("overlay");
    el.style.visibility = (el.style.visibility == "visible") ? "hidden" : "visible";

    const $embed_w = $("#embed-size-width");
    const $embed_h = $("#embed-size-height");
    console.log($embed_w, $embed_h);
    $embed_w.focusout(function() {
        console.log($embed_w.val(), $embed_h.val());
        var w = 800;
        if ($embed_w.val()) {
            var w_ = parseInt($embed_w.val());
            if (!isNaN(w_) && w_ > 0) {
                w = w_;
            } else {
                $embed_w.val(w);
            }
        } else {
            $embed_w.val(w);
        }
        update_embed_value(w, $embed_h.val());
    });
    $embed_h.focus(function() {
        $embed_h.select();
    });
    $embed_w.focus(function() {
        $embed_w.select();
    });
    $embed_h.focusout(function() {
        console.log($embed_w.val(), $embed_h.val());
        var h = 800;
        if ($embed_h.val()) {
            var h_ = parseInt($embed_h.val());
            if (!isNaN(h_) && h_ > 0) {
                h = h_;
            } else {
                $embed_h.val(h);
            }
        } else {
            $embed_h.val(h);
        }
        update_embed_value($embed_w.val(), h);
    });
    $("#embed-html-snippet").focus(function() {
        $(this).select();
    });
}

function update_embed_value(w, h) {
    $("#embed-html-snippet").val("<iframe src=\"" + $("#embed-url").val()
        + "\" width=\"" + w + "\" height=\"" + h + "\" frameborder=\"0\" style=\"border:0\"></iframe>");
}