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

var TRANSPORT = "transport";

var MIN_CLICKABLE_R = 4;

function pnt2layer(map, feature, zoom, result) {
    "use strict";
    var e = feature.geometry.coordinates,
        scaleFactor = Math.pow(2, zoom),
        w = feature.properties.w,
        h;
    if (EDGE == feature.properties.type) {
        return L.polyline(e.map(function (coord) {
            return map.unproject(coord, 1);
        }), {
            color: feature.properties.color,
            opacity: 1,
            weight: w * scaleFactor,
            lineCap: 'round',
            lineJoin: 'round',
            clickable: false,
            fill: false,
            zIndexOffset: -2000,
            riseOnHover: false
        });
    }
    var x = e[0], y = e[1],
        is_bg = -1 !== BG.indexOf(feature.properties.type),
        props = {
            name: feature.properties.name,
            title: feature.properties.name,
            alt: feature.properties.name,
            id: feature.properties.id,
            color: 'white',
            fillColor: feature.properties.color,
            fillOpacity: is_bg ? 0.1 : 1,
            opacity: 1,
            weight: is_bg ? 0 : Math.min(2, w / 10 * Math.pow(2, zoom)),
            fill: true,
            clickable: !is_bg && w * scaleFactor > MIN_CLICKABLE_R,
            zIndexOffset: is_bg ? -2000 : 1000,
            riseOnHover: !is_bg
        },
        bounds,
        centre;
    var node = null;
    if (BG_REACTION == feature.properties.type) {
        h = feature.properties.w;
        bounds = new L.LatLngBounds(map.unproject([x - w, y + h], 1), map.unproject([x + w, y - h], 1));
        return L.rectangle(bounds, props);
    }
    if (BG_COMPARTMENT == feature.properties.type) {
        h = feature.properties.h;
        bounds = new L.LatLngBounds(map.unproject([x - w, y + h], 1), map.unproject([x + w, y - h], 1));
        return L.rectangle(bounds, props);
    }
    if (BG_SPECIES == feature.properties.type) {
        centre = map.unproject([x, y], 1);
        node = L.circleMarker(centre, props);
        node.setRadius(w * scaleFactor / 2);
        return node;
    }
    if (REACTION == feature.properties.type) {
        h = feature.properties.w;
        bounds = new L.LatLngBounds(map.unproject([x - w, y + h], 1), map.unproject([x + w, y - h], 1));
        node = L.rectangle(bounds, props);
    } else if (COMPARTMENT == feature.properties.type) {
        h = feature.properties.h;
        bounds = new L.LatLngBounds(map.unproject([x - w, y + h], 1), map.unproject([x + w, y - h], 1));
        node = L.rectangle(bounds, props);
    } else if (SPECIES == feature.properties.type) {
        centre = map.unproject([x, y], 1);
        node = L.circleMarker(centre, props);
        node.setRadius(w * scaleFactor / 2);
    } else {
        return null;
    }
    node = L.featureGroup([node]);
    w *= scaleFactor;
    if (COMPARTMENT == feature.properties.type){
        w = Math.min(w, h * scaleFactor);
    } else if (SPECIES == feature.properties.type) {
        w /= Math.sqrt(2);
    }
    if (w > 8) {
        centre = map.unproject([x, y], 1);
        var size = Math.max(w * 0.9 / 4, 8),
            label = L.marker(centre,
                            {icon: L.divIcon({
                                    className: 'label',
                                    html: "<span style=\"font-size:" + size + "px;line-height:" + (size + 4) + "px\">" + feature.properties.label + "</span>",
                                    iconSize: [w * 0.89, w * 0.89],
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
    return level >= feature.properties.min_zoom && level <= feature.properties.max_zoom;
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