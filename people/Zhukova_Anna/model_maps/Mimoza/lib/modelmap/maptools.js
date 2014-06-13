/**
 * Created by anna on 12/12/13.
 */


const MARGIN = 156;
const MAP_DIMENSION_SIZE = 512;

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


function adjustMapSize(mapId) {
    const VIEWPORT_MARGIN = 50;
    const MIN_DIMENTION_SIZE = 256;
    var width = Math.max(MIN_DIMENTION_SIZE, $(window).width() - VIEWPORT_MARGIN);
    var height = Math.max(MIN_DIMENTION_SIZE, $(window).height() - VIEWPORT_MARGIN);
    var $map_div = $("#" + mapId);
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
            'maxWidth': width - LEAFLET_POPUP_MARGIN
        });
    }
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


function handlePopUpClosing(map) {
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
}


function initializeMap(jsonData, mapId, maxZoom, cId) {
    var ubLayer = L.layerGroup();
    var tiles = getTiles("lib/modelmap/white512.jpg");
    var gray_tiles =  getTiles("lib/modelmap/gray512.jpg");

    adjustMapSize(mapId);

    var map = L.map(mapId, {
        maxZoom: maxZoom,
        minZoom: 0,
        attributionControl: false,
        padding: [MARGIN, MARGIN],
        layers: [tiles, ubLayer],
        crs: L.CRS.Simple
    }); // .setView([0, 0], 1);

    if (jsonData == null) {
        return map;
    }

    var southWest = map.unproject([0 - MARGIN, MAP_DIMENSION_SIZE + MARGIN], 1);
    var northEast = map.unproject([MAP_DIMENSION_SIZE + MARGIN, 0 - MARGIN], 1);
    var bounds = new L.LatLngBounds(southWest, northEast);
    map.setView(bounds.getCenter(), 0);
    map.setMaxBounds(bounds);

    handlePopUpClosing(map);

    window.onresize = function (event) {
        adjustMapSize(mapId);
    };

    var zMin = -1;
    var zMax = -1;
    for (var z = 0; z <= maxZoom; z++) {
        if (getGeoJson(map, jsonData, z, ubLayer, mapId, cId)) {
            if (-1 == zMin) {
                zMin = z;
            } else {
                zMax = z;
            }
        }
    }

    if (zMin > 0 || zMax < maxZoom) {
        map.on('zoomend', function (e) {
            var zoom = map.getZoom();
            if (zoom < zMin) {
                map.setZoom(zMin);
            } else if (zoom > zMax) {
                map.setZoom(zMin);
            }
        });
    }

    var baseLayers = {
        "White background": tiles,
        "Gray background": gray_tiles
    };
    var overlays = {
        "Ubiquitous species": ubLayer
    };
    L.control.layers(baseLayers, overlays).addTo(map);

    return map;
}

const sp_size = 2.5;
const ub_sp_size = 2;
const r_size = 1.5;

const ub_e_size = 0.5;
const e_size = 0.8;

function get_w(feature) {
    var fType = feature.properties.type;
    if (EDGE == fType) {
        return feature.properties.ubiquitous ? ub_e_size : e_size * feature.properties.size;
    }
    if ((SPECIES == fType) || (BG_SPECIES == fType)) {
//        w /= Math.sqrt(2);
//        h /= Math.sqrt(2);
        return (feature.properties.ubiquitous ? ub_sp_size : sp_size * feature.properties.size) / Math.sqrt(2);
    }
    if ((REACTION == fType) || (BG_REACTION == fType)) {
        return r_size * feature.properties.size;
    }
    return feature.properties.size;
}

function pnt2layer(map, feature, zoom) {
    var e = feature.geometry.coordinates;
	var w = feature.properties.size / 2;
//    var h =  feature.properties.height / 2;
//    var w = get_w(feature) / 2;
    if (EDGE == feature.properties.type) {
        var color = feature.properties.ubiquitous ? GREY : (feature.properties.generalized
            ? (feature.properties.transport ? TURQUOISE : GREEN) : (feature.properties.transport ? VIOLET : BLUE));
        return L.polyline(e.map(function (coord) {
            return map.unproject(coord, 1)
        }), {
            color: color,
            opacity: 1,
            weight: w * Math.pow(2, zoom),
            lineCap: ROUND,
            lineJoin: ROUND,
            clickable: false,
            fill: false,
            zIndexOffset: -2000,
            riseOnHover: false
        });
    }
    var x = e[0], y = e[1];
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
        weight: is_bg ? 0 : Math.min(2, w / 10 * Math.pow(2, zoom)),
        fill: true,
        clickable: !is_bg,
        zIndexOffset: is_bg ? -2000 : 1000,
        riseOnHover: !is_bg
    };
    var southWest = map.unproject([x - w, y + w], 1),
        northEast = map.unproject([x + w, y - w], 1),
        bounds = new L.LatLngBounds(southWest, northEast);
    var scaleFactor = Math.pow(2, zoom);
    var r = w * scaleFactor;
    var centre = map.unproject([x, y], 1);//bounds.getCenter();
    if (BG_SPECIES == feature.properties.type) {
        props["fillColor"] = ORANGE;
        node = L.circleMarker(centre, props);
        node.setRadius(r);
        return node;
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
        node = L.circleMarker(centre, props);
        node.setRadius(r);
    } else {
        return null;
    }
    node = L.featureGroup([node]);
    if (w * scaleFactor * 0.89 >= 10) {
        var size = Math.max(w * scaleFactor * 0.89 / 4, 8);
        var label = L.marker(centre,
            {
                icon: L.divIcon({
                    className: 'label',
                    html: "<span style=\"font-size:" + size + "px;line-height:" + (size + 4) + "px\">" + feature.properties.label + "</span>",
                    iconSize: [w * scaleFactor * 0.89, w * scaleFactor * 0.89],
                    zIndexOffset: -1000,
                    riseOnHover: false
                })
            }
        );
        node.addLayer(label);
    }
    return node;
}


function setAutocomplete(map, tags, name2popup) {
    const searchForm = document.getElementById('search_form');
    if (searchForm != null) {
        var value = searchForm.search_input.value;
        if (tags.indexOf(value) == -1) {
            searchForm.search_input.value = '';
        }
        $("#tags").autocomplete({
            source: tags,
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


function matchesCompartment(cId, feature) {
    var outCompIds = feature.properties.c_outs ? feature.properties.c_outs.split(',') : [];
    return !cId || cId == feature.properties.c_id || outCompIds.indexOf(cId) > -1;
}


function getSpecificJson(map, jsn, name2popup, specific_names, name2selection, level, mapId, cId) {
    return L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, level);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, specific_names, name2selection, feature, layer, mapId);
        },
        filter: function (feature, layer) {
            return !feature.properties.ubiquitous && matchesLevel(level, feature) && matchesCompartment(cId, feature);
        }
    })
}

function getUbiquitousJson(map, jsn, name2popup, specific_names, name2selection, level, mapId, cId) {
    return L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, level);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, specific_names, name2selection, feature, layer, mapId);
        },
        filter: function (feature, layer) {
            return feature.properties.ubiquitous && matchesLevel(level, feature) && matchesCompartment(cId, feature);
        }
    })
}

function matchesLevel(level, feature) {
    return level >= feature.properties.zoom_min && level <= feature.properties.zoom_max
}

function getGeoJson(map, json_data, z, ubLayer, mapId, cId) {
    var name2selection = {};
    var name2popup = {};
    var specific_names = [];

    var sp_json = getSpecificJson(map, json_data, name2popup, specific_names, name2selection, z, mapId, cId);
    var ub_json = getUbiquitousJson(map, json_data, name2popup, specific_names, name2selection, z, mapId, cId);

    var all_names = Object.keys(name2popup);
    if (all_names.length <= 0) {
        return false;
    }

    if (map.getZoom() == z) {
        map.addLayer(sp_json);
        ubLayer.addLayer(ub_json);
        setAutocomplete(map, map.hasLayer(ubLayer) ? all_names : specific_names, name2popup);
    }

    map.on('zoomend', function (e) {
        var zoom = map.getZoom();
        // if we are about to zoom in/out to this geojson
        if (zoom == z) {
            map.addLayer(sp_json);
            ubLayer.addLayer(ub_json);
            setAutocomplete(map, map.hasLayer(ubLayer) ? all_names : specific_names, name2popup);
        } else {
            if (map.hasLayer(sp_json)) {
                map.removeLayer(sp_json);
                ubLayer.removeLayer(ub_json);
            }
        }
    });

    map.on('overlayadd', function(e) {
        if (e.layer == ubLayer && map.getZoom() == z) {
            setAutocomplete(map, all_names, name2popup);
        }
    });
    map.on('overlayremove', function(e) {
        if (e.layer == ubLayer && map.getZoom() == z) {
            setAutocomplete(map, specific_names, name2popup);
        }
    });

    return true;
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