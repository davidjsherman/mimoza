/**
 * Created by anna on 12/12/13.
 */

var UB_LAYER_NAME = "<i>Ubiquitous metabolites</i>",
    OUT_TR_LAYER_NAME = "<i>Transport to outside</i>",
    IN_TR_LAYER_NAME = "<i>Inner transport</i>",
    LEAFLET_POPUP_MARGIN = 10;

function adjustMapSize(mapId) {
    "use strict";
    var VIEWPORT_MARGIN = 50,
        MIN_DIMENTION_SIZE = 256,
        width = Math.max(MIN_DIMENTION_SIZE, ($(window).width() - VIEWPORT_MARGIN)),
        height = Math.max(MIN_DIMENTION_SIZE, Math.round(($(window).height() - VIEWPORT_MARGIN) * 0.7));
    return adjustMapDivSize(mapId, width, height);
}

function adjustMapDivSize(mapId, width, height) {
    "use strict";
    var $map_div = $("#" + mapId),
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

function updateMapBounds(coords, commonCoords, map) {
    coords[0][0] = coords[0][0] == null ? commonCoords[0][0] : Math.min(coords[0][0], commonCoords[0][0]);
    coords[0][1] = coords[0][1] == null ? commonCoords[0][1] : Math.max(coords[0][1], commonCoords[0][1]);
    coords[1][0] = coords[1][0] == null ? commonCoords[1][0] : Math.max(coords[1][0], commonCoords[1][0]);
    coords[1][1] = coords[1][1] == null ? commonCoords[1][1] : Math.min(coords[1][1], commonCoords[1][1]);

    var mapW = coords[1][0] - coords[0][0],
        mapH = coords[0][1] - coords[1][1],
        margin = Math.max(mapW, mapH) * 0.1;

    coords[0][0] -= margin;
    coords[0][1] += margin;
    coords[1][0] += margin;
    coords[1][1] -= margin;

    map.setMaxBounds(coords);
}

function initializeMap(cId2jsonData, mapId, compIds, cId2outside) {
    "use strict";
    var size = adjustMapSize(mapId),
        layers = [],
        minZoom = Math.max(1, Math.round(size / MAP_DIMENSION_SIZE)),
        ubLayer = L.layerGroup(),
        overlays = {},
        cIds = {},
        cId = getParameter("id"),
        inZoom = getParameter("zoom"),
        curZoom = inZoom == null ? minZoom + 1 : minZoom + 2,
        outCId = null,
        jsonData;
    if (cId == null && compIds && typeof Object.keys(compIds) !== 'undefined' && Object.keys(compIds).length > 0) {
        cId = Object.keys(compIds)[0];
    }
    if (cId != null) {
        cIds[cId] = compIds[cId];
        jsonData = cId2jsonData[cId];
        $("#comp").html(compIds[cId]);
        if (cId in cId2outside) {
            outCId = cId2outside[cId];
        }
    }
    if (typeof jsonData === 'undefined' || jsonData.length <= 0) {
        return null;
    }
    var maxZoom = 7 + minZoom,
        tiles = getTiles("lib/modelmap/white.jpg", minZoom, maxZoom),
        grayTiles = getTiles("lib/modelmap/gray.jpg", minZoom, maxZoom),
        outTransportLayer = L.layerGroup(),
        inTransportLayer = L.layerGroup(),
        compLayer = L.layerGroup();
    layers.push(ubLayer);
    layers.push(tiles);
    layers.push(compLayer);
    // layers.push(outTransportLayer);
    layers.push(inTransportLayer);
    var map = L.map(mapId, {
        maxZoom: maxZoom,
        minZoom: outCId != null ? minZoom - 1 : minZoom,
        zoom: curZoom,
        attributionControl: false,
        padding: [MARGIN, MARGIN],
        layers: layers,
        crs: L.CRS.Simple
    });
    handlePopUpClosing(map);
    var name2popup = {},
        name2zoom = {},
        maxLoadedZoom = inZoom == null ? minZoom + 1 : minZoom + 7,
        coords = [
            [null, null],
            [null, null]
        ],
        commonCoords = [
            [null, null],
            [null, null],
            null
        ],
        ubJSON = false,
        inJSON = false,
        outJSON = false,
        jsonArray;

    function loadElements(json, fromZoom, toZoom, coords) {
        jsonArray = loadGeoJson(map, json, fromZoom, toZoom, ubLayer, compLayer, mapId, cId, name2popup, name2zoom, coords, minZoom, inZoom);
        ubJSON |= jsonArray[1];
        jsonArray = loadGeoJson(map, json, fromZoom, toZoom, ubLayer, outTransportLayer, mapId, TRANSPORT, name2popup, name2zoom, coords, minZoom, inZoom);
        ubJSON |= jsonArray[1];
        outJSON |= jsonArray[0] || jsonArray[1];
        jsonArray = loadGeoJson(map, json, fromZoom, toZoom, ubLayer, inTransportLayer, mapId, INNER_TRANSPORT, name2popup, name2zoom, coords, minZoom, inZoom);
        ubJSON |= jsonArray[1];
        inJSON |= jsonArray[0] || jsonArray[1];
    }

    // load common elements
    loadElements(jsonData[0], minZoom, maxZoom, commonCoords);
    // load generalized elements
    loadElements(jsonData[1], minZoom, minZoom + 1, coords);

    if (curZoom > minZoom + 1) {
        loadElements(jsonData[2], minZoom + 2, maxZoom, coords);
    }

    updateMapBounds(coords, commonCoords, map);
    map.setView(commonCoords[2], curZoom);

    var $map_div = $("#" + mapId);
    $map_div.bind('resize', function(){
        var h = $map_div.height(),
            w = $map_div.width();
        $(".leaflet-popup").css({
            'maxHeight': h,
            'maxWidth': w
        });
        $(".leaflet-popup-content").css({
            'maxHeight': h - LEAFLET_POPUP_MARGIN,
            'maxWidth': w - LEAFLET_POPUP_MARGIN
        });
        map.invalidateSize();
        map.setView(map.getCenter(), map.getZoom());
    });

    if (ubJSON) {
        overlays[UB_LAYER_NAME] = ubLayer;
    }
    if (outJSON) {
        overlays[OUT_TR_LAYER_NAME] = outTransportLayer;
    }
    if (inJSON) {
        overlays[IN_TR_LAYER_NAME] = inTransportLayer;
    }
    var baseLayers = {
        "White background": tiles,
        "Gray background": grayTiles
        },
        control = L.control.layers(baseLayers, overlays);
    control.addTo(map);

    initializeAutocomplete(name2popup, name2zoom, map);

    map.on('zoomend', function (e) {
        if (outCId != null && map.getZoom() == map.getMinZoom()) {
            window.location.href = "?id=" + outCId + (cId == null ? "" : ("&zoom=" + cId));
        }
        // if we are about to zoom in/out to this geojson
        if (map.getZoom() > maxLoadedZoom) {
            // load specific elements
            loadElements(jsonData[2], minZoom + 2, maxZoom, coords);
            updateMapBounds(coords, commonCoords, map);
            var updateControl = false;
            if (!overlays.hasOwnProperty(UB_LAYER_NAME) && ubJSON) {
                overlays[UB_LAYER_NAME] = ubLayer;
                updateControl = true;
            }
            // outside transport should already be visible on the general zoom level,
            // so no need to update the control
            if (!overlays.hasOwnProperty(IN_TR_LAYER_NAME) && inJSON) {
                overlays[IN_TR_LAYER_NAME] = inTransportLayer;
                updateControl = true;
            }
            if (updateControl) {
                control.removeFrom(map);
                control = L.control.layers(baseLayers, overlays);
                control.addTo(map);
            }
            maxLoadedZoom = maxZoom;
            initializeAutocomplete(name2popup, name2zoom, map);
        }
    });
    return map;
}


function initializeAutocomplete(name2popup, name2zoom, map) {
    "use strict";
    var searchForm = document.getElementById('search_form');
    if (searchForm !== null) {
        var $tags = $("#tags");
        $tags.autocomplete({
            source: Object.keys(name2popup),
            autoFocus: true
        });
        $tags.keypress(function (e) {
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


function getParameter(name){
  var regexS = "[\\?&]" + name + "=([^&#]*)";
  var regex = new RegExp(regexS);
  var results = regex.exec(window.location.href);
  if(results == null)
    return null;
  else
    return results[1];
}


function update_embed_value(w, h) {
    "use strict";
    var cId = getParameter(),
        url = $("#embed-url").val();
    if (cId) {
        url += "?id=" + cId;
    }
    $("#embed-html-snippet").val("<iframe src=\"" + url + "\" width=\"" + w + "\" height=\"" + h
        + "\" frameborder=\"0\" style=\"border:0\"></iframe>");
}