/**
 * Created by anna on 12/12/13.
 */

function adjustMapSize(mapId) {
    "use strict";
    var VIEWPORT_MARGIN = 50,
        MIN_DIMENTION_SIZE = 256,
        LEAFLET_POPUP_MARGIN = 10,
        width = Math.max(MIN_DIMENTION_SIZE, ($(window).width() - VIEWPORT_MARGIN)),
        height = Math.max(MIN_DIMENTION_SIZE, Math.round(($(window).height() - VIEWPORT_MARGIN) * 0.7)),
        $map_div = $("#" + mapId),
        old_height = $map_div.height(),
        old_width = $map_div.width();
    if (old_width != width || old_height != height) {
        $map_div.css({
            'height': height,
            'width': width
        });
        $(".leaflet-popup").css({
            'maxHeight': height,
            'maxWidth': width
        });
        $(".leaflet-popup-content").css({
            'maxHeight': height - LEAFLET_POPUP_MARGIN,
            'maxWidth': width - LEAFLET_POPUP_MARGIN
        });
    }
    return Math.min(width, height);
}

function getTiles(img, minZoom, maxZoom) {
    "use strict";
    return L.tileLayer(img, {
        continuousWorld: true,
        noWrap: true,
        tileSize: 256,
        maxZoom: maxZoom,
        minZoom: minZoom,
        tms: true,
        updateWhenIdle: true,
        reuseTiles: true
    });
}

function handlePopUpClosing(map) {
    "use strict";
    var popup = null;
    map.on('popupopen', function (e) {
        popup = e.popup;
    });
    map.on('dragstart', function (e) {
        if (popup) {
            map.closePopup(popup);
            popup.options.keepInView = false;
            map.openPopup(popup);
            popup.options.keepInView = true;
            popup = null;
        }
    });
}

function initializeMap(cId2jsonData, mapId, compIds) {
    "use strict";
    var size = adjustMapSize(mapId),
        layers = [],
        minZoom = size == MAP_DIMENSION_SIZE / 2 ? 0 : Math.round(size / MAP_DIMENSION_SIZE),
        ubLayer = L.layerGroup(),
        overlays = {},
        cIds = {},
        cId = gup(),
        jsonData;
    if (cId == null && compIds && typeof Object.keys(compIds) !== 'undefined' && Object.keys(compIds).length > 0) {
        cId = Object.keys(compIds)[0];
    }
    if (cId != null) {
        cIds[cId] = compIds[cId];
        jsonData = cId2jsonData[cId];
        $("#comp").html(compIds[cId]);
    }
    if (typeof jsonData === 'undefined' || jsonData.length <= 0) {
        return null;
    }
    var maxZoom = 4 + minZoom,//jsonData.length - 1 + minZoom,
        tiles = getTiles("lib/modelmap/white.jpg", minZoom, maxZoom),
        grayTiles =  getTiles("lib/modelmap/gray.jpg", minZoom, maxZoom),
        transportLayer = L.layerGroup(),
        compLayer = L.featureGroup();
    layers.push(ubLayer);
    layers.push(tiles);
    layers.push(compLayer);
    layers.push(transportLayer);
    var map = L.map(mapId, {
        maxZoom: maxZoom,
        minZoom: minZoom,
        attributionControl: false,
        padding: [MARGIN, MARGIN],
        layers: layers,
        crs: L.CRS.Simple
    });
    handlePopUpClosing(map);
    window.onresize = function (event) {
        adjustMapSize(mapId);
    };
    var name2popup = {},
        name2zoom = {},
        json,
        z = minZoom,
        maxLoadedZoom = minZoom,
        coords = [[null, null], [null, null]];
    json = jsonData[0];
    loadGeoJson(map, json, minZoom, ubLayer, compLayer, mapId, cId, name2popup, name2zoom, coords);
    loadGeoJson(map, json, minZoom, ubLayer, transportLayer, mapId, TRANSPORT, name2popup, name2zoom, coords);

    var margin = Math.max(coords[1][0] - coords[0][0], coords[0][1] - coords[1][1]) * 0.1;
    coords[0][0] -= margin;
    coords[0][1] += margin;
    coords[1][0] += margin;
    coords[1][1] -= margin;
    map.setMaxBounds(coords);
    map.fitBounds(coords);

    initializeAutocomplete(name2popup, name2zoom, map);
    map.on('zoomend', function (e) {
        var zoom = map.getZoom(),
            mZoom = Math.min(zoom + 1, maxZoom);
        // if we are about to zoom in/out to this geojson
        if (zoom > maxLoadedZoom) {
	        for (z = maxLoadedZoom + 1; z <= mZoom; z += 2) {
//	        for (z = maxLoadedZoom + 1; z <= mZoom; z += 1) {
	            json = jsonData[(z + 1 - minZoom) / 2];
//	            json = jsonData[z - minZoom];
                loadGeoJson(map, json, z, ubLayer, compLayer, mapId, cId, name2popup, name2zoom, coords);
                loadGeoJson(map, json, z + 1, ubLayer, compLayer, mapId, cId, name2popup, name2zoom, coords);
                loadGeoJson(map, json, z, ubLayer, transportLayer, mapId, TRANSPORT, name2popup, name2zoom, coords);
                loadGeoJson(map, json, z + 1, ubLayer, transportLayer, mapId, TRANSPORT, name2popup, name2zoom, coords);
            }
	        maxLoadedZoom = mZoom;
	        initializeAutocomplete(name2popup, name2zoom, map);
        }
    });
    var baseLayers = {
        "White background": tiles,
        "Gray background": grayTiles
    };
    overlays["<i>Ubiquitous species</i>"] = ubLayer;
    overlays["<i>Transport reactions</i>"] = transportLayer;
    L.control.layers(baseLayers, overlays).addTo(map);
    return map;
}


function initializeAutocomplete(name2popup, name2zoom, map) {
    "use strict";
    var searchForm = document.getElementById('search_form');
    if (searchForm !== null) {
        $("#tags").autocomplete({
            source: Object.keys(name2popup),
            autoFocus: true
        });
        $('#tags').keypress(function (e) {
            var code = e.keyCode || e.which;
            if (code === $.ui.keyCode.ENTER) {
                search(map, name2popup, name2zoom);
                e.preventDefault();
            }
        });
        searchForm.onclick = function () {
            search(map, name2popup, name2zoom);
        };
    }
}

function centerMap() {
    "use strict";
    map.setView([0, 0], map.getZoom());
}

function overlay() {
    "use strict";
    var el = document.getElementById("overlay");
    var $embed_w = $("#embed-size-width"),
        $embed_h = $("#embed-size-height");
    update_embed_value($embed_w.val(), $embed_h.val());
    el.style.visibility = (el.style.visibility === "visible") ? "hidden" : "visible";
    $embed_w.focusout(function() {
        var w = 800;
        if ($embed_w.val()) {
            var newW = parseInt($embed_w.val());
            if (!isNaN(newW) && newW > 0) {
                w = newW;
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
            var newH = parseInt($embed_h.val());
            if (!isNaN(newH) && newH > 0) {
                h = newH;
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


function gup(){
  var regexS = "[\\?&]id=([^&#]*)";
  var regex = new RegExp(regexS);
  var results = regex.exec(window.location.href);
  if(results == null)
    return null;
  else
    return results[1];
}


function update_embed_value(w, h) {
    "use strict";
    var cId = gup(),
        url = $("#embed-url").val();
    if (cId) {
        url += "?id=" + cId;
    }
    $("#embed-html-snippet").val("<iframe src=\"" + url + "\" width=\"" + w + "\" height=\"" + h
        + "\" frameborder=\"0\" style=\"border:0\"></iframe>");
}