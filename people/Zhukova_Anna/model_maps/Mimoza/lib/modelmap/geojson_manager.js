/**
 * Created by anna on 6/17/14.
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

const TRANSPORT = "transport";

function pnt2layer(map, feature, zoom, result) {
    var e = feature.geometry.coordinates;
    var w = feature.properties.w / 2;
    var h = feature.properties.h / 2;
    var s = feature.properties.size / 2;
    var scaleFactor = Math.pow(2, zoom);
    if (EDGE == feature.properties.type) {
        var color = feature.properties.ubiquitous ? GREY : (feature.properties.generalized
            ? (feature.properties.transport ? TURQUOISE : GREEN) : (feature.properties.transport ? VIOLET : BLUE));
        return L.polyline(e.map(function (coord) {
            return map.unproject(coord, 1)
        }), {
            color: color,
            opacity: 1,
            weight: s / 2 * scaleFactor,
            lineCap: ROUND,
            lineJoin: ROUND,
            clickable: false,
            fill: false,
            zIndexOffset: -2000,
            riseOnHover: false
        });
    }
    var r = Math.min(w, h) * scaleFactor;
    var big_enough = r > 10;
    var x = e[0], y = e[1];
    var is_bg = -1 != BG.indexOf(feature.properties.type);
    var props = {
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
        clickable: !is_bg && big_enough,
        zIndexOffset: is_bg ? -2000 : 1000,
        riseOnHover: !is_bg
    };
    var southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1),
        bounds = new L.LatLngBounds(southWest, northEast);
//    r = southWest.distanceTo(northEast) / 2;
    var centre = map.unproject([x, y], 1);//bounds.getCenter();
    if (BG_SPECIES == feature.properties.type) {
        props["fillColor"] = ORANGE;
        node = L.circleMarker(centre, props);
        node.setRadius(r/2);
        return node;
//        return L.rectangle(bounds, props);
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
        node.setRadius(r/2);
//        node = L.rectangle(bounds, props);
    } else {
        return null;
    }
    node = L.featureGroup([node]);
    if (big_enough) {
        if (SPECIES == feature.properties.type) {
            r /= Math.sqrt(2);
        }
        var size = Math.max(r * 0.9 / 4, 8);
        var label = L.marker(centre,
            {
                icon: L.divIcon({
                    className: 'label',
                    html: "<span style=\"font-size:" + size + "px;line-height:" + (size + 4) + "px\">" + feature.properties.label + "</span>",
                    iconSize: [r * 0.89, r * 0.89],
                    zIndexOffset: -1000,
                    riseOnHover: false
                })
            }
        );
        node.addLayer(label);
    }
    result[0] = true;
    return node;
}

function matchesCompartment(cId, feature) {
    if (TRANSPORT == cId) {
        return feature.properties.transport;
    }
    return cId == feature.properties.c_id || cId == feature.properties.id;
}

function matchesLevel(level, feature) {
    return level >= feature.properties.zoom_min && level <= feature.properties.zoom_max
}

function rescaleZoom(zMin, level) {
    return -1 == zMin ? 0 : level - zMin;
}

function getFilteredJson(map, jsn, name2popup, name2zoom, zoom, realZoom, mapId, result, filterFunction) {
    const name2selection = {};
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
    })
}

function getGeoJson(map, json_data, z, ubLayer, compLayer, mapId, cId, zMin, name2popup, name2zoom) {
    var result=[false];
    const zz = rescaleZoom(zMin, z);

    var specificJson = getFilteredJson(map, json_data, name2popup, name2zoom, zz, z, mapId, result,
        function (feature) {
            return !feature.properties.ubiquitous && matchesLevel(z, feature) && matchesCompartment(cId, feature);
        }
    );
    var ubiquitousJson = getFilteredJson(map, json_data, name2popup, name2zoom, zz, z, mapId, result,
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
        if (e.layer == ubLayer && map.getZoom() == zz) {
            compLayer.addLayer(ubiquitousJson);
        }
    });

    map.on('overlayremove', function(e) {
        if (e.layer == ubLayer && map.getZoom() == zz) {
            compLayer.removeLayer(ubiquitousJson);
        }
    });

    return true;
}