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

function initializeMap(jsonData, mapId, maxZoom, cId) {
    var ubLayer = L.layerGroup();
    var tiles = getTiles("lib/modelmap/white.jpg");
    var gray_tiles =  getTiles("lib/modelmap/gray.jpg");

    adjustMapSize(mapId);

    var map = L.map(mapId, {
        maxZoom: maxZoom,
        minZoom: 0,
        attributionControl: false,
        padding: [MARGIN, MARGIN],
        layers: [tiles, ubLayer],
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
    for (var z = 0; z <= maxZoom; z++) {
        if (getGeoJson(map, jsonData, z, ubLayer, mapId, cId, zMin)) {
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
    var overlays = {
        "Ubiquitous species": ubLayer
    };
    L.control.layers(baseLayers, overlays).addTo(map);

    return map;
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