/**
 * Created by anna on 12/12/13.
 */

function adjustMapSize(mapId) {
    "use strict";
    var VIEWPORT_MARGIN = 50,
        MIN_DIMENTION_SIZE = 256,
        LEAFLET_POPUP_MARGIN = 10,
        width = Math.max(MIN_DIMENTION_SIZE, $(window).width() - VIEWPORT_MARGIN),
        height = Math.max(MIN_DIMENTION_SIZE, $(window).height() - VIEWPORT_MARGIN),
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

function initializeMap(cId2jsonData, mapId, maxZoom, compIds) {
    "use strict";
    var layers = [],
        minZoom = Math.round(Math.min($(window).width(), $(window).height()) / MAP_DIMENSION_SIZE),
        ubLayer = L.layerGroup(),
        tiles = getTiles("lib/modelmap/white.jpg", minZoom, maxZoom + minZoom),
        grayTiles =  getTiles("lib/modelmap/gray.jpg", minZoom, maxZoom + minZoom),
        overlays = {},
        cIds = {},
        cId = gup(),
        jsonData,
        transportLayer = L.layerGroup(),
        compLayer = L.layerGroup();
    maxZoom += minZoom;
    layers.push(ubLayer);
    layers.push(grayTiles);
    layers.push(compLayer);
    layers.push(transportLayer);
    adjustMapSize(mapId);
//    cIds[TRANSPORT] = "<i>Transport reactions</i>";
    if (cId == null && compIds && typeof Object.keys(compIds) !== 'undefined' && Object.keys(compIds).length > 0) {
        cId = Object.keys(compIds)[0];
    }
    if (cId != null) {
        cIds[cId] = compIds[cId];
        jsonData = cId2jsonData[cId];
        $("#comp").html(compIds[cId]);
    }
//    for (cId in cIds) {
//        var cLayer = L.layerGroup();
//        layers.push(cLayer);
//        overlays[cIds[cId]] = cLayer;
//    }
    var map = L.map(mapId, {
        maxZoom: maxZoom,
        minZoom: minZoom,
        attributionControl: false,
        padding: [MARGIN, MARGIN],
        layers: layers,
        crs: L.CRS.Simple
    });
    if (typeof jsonData === 'undefined' || jsonData.length <= 0) {
        return map;
    }
    var southWest = map.unproject([0 - MARGIN, MAP_DIMENSION_SIZE + MARGIN], 1),
        northEast = map.unproject([MAP_DIMENSION_SIZE + MARGIN, 0 - MARGIN], 1),
        bounds = new L.LatLngBounds(southWest, northEast);
    map.setMaxBounds(bounds);
    handlePopUpClosing(map);
    window.onresize = function (event) {
        adjustMapSize(mapId);
    };
    var name2popup = {},
        name2zoom = {},
        json,
        z = minZoom,
        maxLoadedZoom = Math.min(1 + minZoom, maxZoom);
    for (z = minZoom; z <= maxLoadedZoom; z++) {
        json = jsonData[z - minZoom];
        if (cId) {
            loadGeoJson(map, json, z, ubLayer, compLayer, mapId, cId, name2popup, name2zoom);
        }
        loadGeoJson(map, json, z, ubLayer, transportLayer, mapId, TRANSPORT, name2popup, name2zoom);
//        for (cId in cIds) {
//            compLayer = overlays[cIds[cId]];
//            loadGeoJson(map, json, z, ubLayer, compLayer, mapId, cId, name2popup, name2zoom);
//        }
    }
    initializeAutocomplete(name2popup, name2zoom, map);
    map.on('zoomend', function (e) {
        var zoom = map.getZoom(),
            mZoom = Math.min(zoom + 1, maxZoom);
        // if we are about to zoom in/out to this geojson
        if (zoom > maxLoadedZoom) {
	        for (z = maxLoadedZoom + 1; z <= mZoom; z++) {
	            json = jsonData[z - minZoom];
                if (cId) {
                    loadGeoJson(map, json, z, ubLayer, compLayer, mapId, cId, name2popup, name2zoom);
                }
                loadGeoJson(map, json, z, ubLayer, transportLayer, mapId, TRANSPORT, name2popup, name2zoom);
//	            for (cId in cIds) {
//	                compLayer = overlays[cIds[cId]];
//	                loadGeoJson(map, json, z, ubLayer, compLayer, mapId, cId, name2popup, name2zoom);
//	            }
	        }
	        maxLoadedZoom = mZoom;
	        initializeAutocomplete(name2popup, name2zoom, map);
        }
    });
    map.setView([MAP_DIMENSION_SIZE / 4 * (minZoom + 1), MAP_DIMENSION_SIZE / 4 * (minZoom + 1)], minZoom);
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
    el.style.visibility = (el.style.visibility === "visible") ? "hidden" : "visible";
    var $embed_w = $("#embed-size-width"),
        $embed_h = $("#embed-size-height");
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
    $("#embed-html-snippet").val("<iframe src=\"" + $("#embed-url").val()
        + "\" width=\"" + w + "\" height=\"" + h + "\" frameborder=\"0\" style=\"border:0\"></iframe>");
}