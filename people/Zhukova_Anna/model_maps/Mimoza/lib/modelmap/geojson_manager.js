/**
 * Created by anna on 6/17/14.
 */

var MARGIN = 156;
var MAP_DIMENSION_SIZE = 512;

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
var WHITE = 'white';

var ROUND = 'round';

var TRANSPORT = "transport";

var MIN_CLICKABLE_R = 4;

function pnt2layer(map, feature, zoom, result) {
    "use strict";
    var e = feature.geometry.coordinates,
        scaleFactor = Math.pow(2, zoom);
    if (EDGE == feature.properties.type) {
        var color = feature.properties.ubiquitous ? GREY : (feature.properties.generalized
            ? (feature.properties.transport ? TURQUOISE : GREEN) : (feature.properties.transport ? VIOLET : BLUE));
        return L.polyline(e.map(function (coord) {
            return map.unproject(coord, 1);
        }), {
            color: color,
            opacity: 1,
            weight: (feature.properties.size / 4) * scaleFactor,
            lineCap: ROUND,
            lineJoin: ROUND,
            clickable: false,
            fill: false,
            zIndexOffset: -2000,
            riseOnHover: false
        });
    }
    var w = feature.properties.w / 2,
        h = feature.properties.h / 2,
        r = Math.min(w, h) * scaleFactor,
        x = e[0], y = e[1],
        is_bg = -1 !== BG.indexOf(feature.properties.type),
        props = {
            name: feature.properties.name,
            title: feature.properties.name,
            alt: feature.properties.name,
            id: feature.properties.id,
            color: WHITE,
            fillOpacity: is_bg ? 0.1 : 1,
            opacity: 1,
            lineCap: ROUND,
            lineJoin: ROUND,
            weight: is_bg ? 0 : Math.min(2, w / 10 * Math.pow(2, zoom)),
            fill: true,
            clickable: !is_bg && r > MIN_CLICKABLE_R,
            zIndexOffset: is_bg ? -2000 : 1000,
            riseOnHover: !is_bg
        },
        southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1),
        bounds = new L.LatLngBounds(southWest, northEast),
        centre = map.unproject([x, y], 1);
    var node = null;
    if (BG_SPECIES == feature.properties.type) {
        props.fillColor = ORANGE;
        node = L.circleMarker(centre, props);
        node.setRadius(r / 2);
        return node;
    }
    if (BG_REACTION == feature.properties.type) {
        props.fillColor = feature.properties.transport ? TURQUOISE : GREEN;
        return L.rectangle(bounds, props);
    }
    if (BG_COMPARTMENT == feature.properties.type) {
        props.fillColor = YELLOW;
        return L.rectangle(bounds, props);
    }
    if (REACTION == feature.properties.type) {
        props.fillColor = feature.properties.generalized ? (feature.properties.transport ? TURQUOISE : GREEN) : (feature.properties.transport ? VIOLET : BLUE);
        node = L.rectangle(bounds, props);
    } else if (COMPARTMENT == feature.properties.type) {
        props.fillColor = YELLOW;
        node = L.rectangle(bounds, props);
    } else if (SPECIES == feature.properties.type) {
        props.fillColor = feature.properties.ubiquitous ? GREY : (feature.properties.generalized ? ORANGE : RED);
        node = L.circleMarker(centre, props);
        node.setRadius(r / 2);
    } else {
        return null;
    }
    node = L.featureGroup([node]);
    if (r > 8) {
        if (SPECIES == feature.properties.type) {
            r /= Math.sqrt(2);
        }
        var size = Math.max(r * 0.9 / 4, 8),
            label = L.marker(centre,
                            {icon: L.divIcon({
                                    className: 'label',
                                    html: "<span style=\"font-size:" + size + "px;line-height:" + (size + 4) + "px\">" + feature.properties.label + "</span>",
                                    iconSize: [r * 0.89, r * 0.89],
                                    zIndexOffset: -1000,
                                    riseOnHover: false})
                            }
            );
        node.addLayer(label);
    }
    result[0] = true;
    return node;
}

function matchesCompartment(cId, feature) {
    "use strict";
    if (TRANSPORT == cId) {
        return feature.properties.transport;
    }
    return cId == feature.properties.c_id || cId == feature.properties.id;
}

function matchesLevel(level, feature) {
    "use strict";
    return level >= feature.properties.zoom_min && level <= feature.properties.zoom_max;
}

function rescaleZoom(zMin, level) {
    "use strict";
    return -1 === zMin ? 0 : level - zMin;
}

function getFilteredJson(map, jsn, name2popup, name2zoom, zoom, realZoom, mapId, result, filterFunction) {
    "use strict";
    var name2selection = {};
    return L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, zoom, result);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, name2zoom, name2selection, feature, layer, mapId, zoom, realZoom);
        },
        filter: function (feature, layer) {
            return filterFunction(feature);
        }
    });
}

function getGeoJson(map, json_data, z, ubLayer, compLayer, mapId, cId, zMin, name2popup, name2zoom) {
    "use strict";
    var result = [false],
        zz = rescaleZoom(zMin, z),
        specificJson = getFilteredJson(map, json_data, name2popup, name2zoom, zz, z, mapId, result,
            function (feature) {
                return !feature.properties.ubiquitous && matchesLevel(z, feature) && matchesCompartment(cId, feature);
            }
        ),
        ubiquitousJson = getFilteredJson(map, json_data, name2popup, name2zoom, zz, z, mapId, result,
            function (feature) {
                return feature.properties.ubiquitous && matchesLevel(z, feature) && matchesCompartment(cId, feature);
            }
        );
    if (!result[0]) {
        return false;
    }
    if (map.getZoom() == zz) {
        compLayer.addLayer(specificJson);
        if (map.hasLayer(ubLayer)) {
            compLayer.addLayer(ubiquitousJson);
        }
    }
    map.on('zoomend', function (e) {
        var zoom = map.getZoom();
        // if we are about to zoom in/out to this geojson
        if (zoom == zz) {
            compLayer.addLayer(specificJson);
            if (map.hasLayer(ubLayer)) {
                compLayer.addLayer(ubiquitousJson);
            }
        } else {
            if (compLayer.hasLayer(specificJson)) {
                compLayer.removeLayer(specificJson);
                if (map.hasLayer(ubLayer)) {
                    compLayer.removeLayer(ubiquitousJson);
                }
            }
        }
    });
    map.on('overlayadd', function(e) {
        if (e.layer === ubLayer && map.getZoom() == zz) {
            compLayer.addLayer(ubiquitousJson);
        }
    });
    map.on('overlayremove', function(e) {
        if (e.layer === ubLayer && map.getZoom() == zz) {
            compLayer.removeLayer(ubiquitousJson);
        }
    });
    return true;
}