/**
 * Created by anna on 12/12/13.
 */

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
        tileSize: 256,
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

function initializeMap(jsonData, mapId, maxZoom, cIds) {
    var layers = [];
    var ubLayer = L.layerGroup();
    layers.push(ubLayer);

    var tiles = getTiles("lib/modelmap/white.jpg");
    var gray_tiles =  getTiles("lib/modelmap/gray.jpg");
    layers.push(gray_tiles);

    adjustMapSize(mapId);

    cIds[TRANSPORT] = "<i>Transport reactions</i>";

    var overlays = {};
    for (var cId in cIds) {
        var cLayer = L.layerGroup();
        layers.push(cLayer);
        overlays[cIds[cId]] = cLayer;
    }

    var map = L.map(mapId, {
        maxZoom: maxZoom,
        minZoom: 0,
        attributionControl: false,
        padding: [MARGIN, MARGIN],
        layers: layers,
        crs: L.CRS.Simple
    });

    if (jsonData == null) {
        return map;
    }

    var southWest = map.unproject([0 - MARGIN, MAP_DIMENSION_SIZE + MARGIN], 1);
    var northEast = map.unproject([MAP_DIMENSION_SIZE + MARGIN, 0 - MARGIN], 1);
    var bounds = new L.LatLngBounds(southWest, northEast);
    map.setMaxBounds(bounds);

    handlePopUpClosing(map);

    window.onresize = function (event) {
        adjustMapSize(mapId);
    };


    var zMin = -1;
    var zMax = -1;

    var name2popup = {};
    var name2zoom = {};
    for (var z = 0; z <= maxZoom; z++) {
        for (cId in cIds) {
            var compLayer = overlays[cIds[cId]];
            if (getGeoJson(map, jsonData, z, ubLayer, compLayer, mapId, cId, zMin, name2popup, name2zoom)) {
                if (-1 == zMin) {
                    zMin = z;
                } else {
                    zMax = z;
                }
            }
        }
    }

    initializeAutocomplete(name2popup, name2zoom, map);

    if (zMin > 0 || zMax < maxZoom) {
        map.on('zoomend', function (e) {
            var zoom = map.getZoom();
            if (zoom > zMax - zMin) {
                map.setZoom(zMax - zMin);
            }
        });
    }
    map.setView([0, 0], zMin);

    var baseLayers = {
        "White background": tiles,
        "Gray background": gray_tiles
    };
    overlays["<i>Ubiquitous species</i>"] = ubLayer;
    L.control.layers(baseLayers, overlays).addTo(map);

    return map;
}


function initializeAutocomplete(name2popup, name2zoom, map) {
    const searchForm = document.getElementById('search_form');
    if (searchForm != null) {
        $("#tags").autocomplete({
            source: Object.keys(name2popup),
            autoFocus: true
        });
        $('#tags').keypress(function (e) {
            var code = (e.keyCode ? e.keyCode : e.which);
            if (code == $.ui.keyCode.ENTER) {
                search(map, name2popup, name2zoom);
                e.preventDefault();
            }
        });
        searchForm.onclick = function () {
            search(map, name2popup, name2zoom);
        };
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
    $embed_w.focusout(function() {
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