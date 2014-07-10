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

//const SPECIES_SIZE = 2.5;
//const UB_SPECIES_SIZE = 2;
//const REACTION_SIZE = 1.5;
//
//const UB_EDGE_SIZE = 0.5;
//const EDGE_SIZE = 0.8;

function getSize(feature) {
    return feature.properties.size;

//    var fType = feature.properties.type;
//    if (EDGE == fType) {
//        return feature.properties.ubiquitous ? UB_EDGE_SIZE : EDGE_SIZE * feature.properties.size;
//    }
//    if ((SPECIES == fType) || (BG_SPECIES == fType)) {
//        return (feature.properties.ubiquitous ? UB_SPECIES_SIZE : SPECIES_SIZE * feature.properties.size) / Math.sqrt(2);
//    }
//    if ((REACTION == fType) || (BG_REACTION == fType)) {
//        return REACTION_SIZE * feature.properties.size;
//    }
//    return feature.properties.size;
}

function pnt2layer(map, feature, zoom, result) {
    var e = feature.geometry.coordinates;
    var w = getSize(feature) / 2;
    var scaleFactor = Math.pow(2, zoom);
    if (EDGE == feature.properties.type) {
        var color = feature.properties.ubiquitous ? GREY : (feature.properties.generalized
            ? (feature.properties.transport ? TURQUOISE : GREEN) : (feature.properties.transport ? VIOLET : BLUE));
        return L.polyline(e.map(function (coord) {
            return map.unproject(coord, 1)
        }), {
            color: color,
            opacity: 1,
            weight: w / 2 * scaleFactor,
            lineCap: ROUND,
            lineJoin: ROUND,
            clickable: false,
            fill: false,
            zIndexOffset: -2000,
            riseOnHover: false
        });
    }
    var r = w * scaleFactor;
    var big_enough = r > 10;
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
        clickable: !is_bg && big_enough,
        zIndexOffset: is_bg ? -2000 : 1000,
        riseOnHover: !is_bg
    };
    var southWest = map.unproject([x - w, y + w], 1),
        northEast = map.unproject([x + w, y - w], 1),
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
        var size = Math.max(r * 0.89 / 4, 8);
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

function getFilteredJson(map, jsn, name2popup, specific_names, name2selection, level, mapId, zMin, result, filterFunction) {
    var zoom = rescaleZoom(zMin, level);
    return L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, zoom, result);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, specific_names, name2selection, feature, layer, mapId, zoom);
        },
        filter: function (feature, layer) {
            return filterFunction(feature);
        }
    })
}

function getGeoJson(map, json_data, z, ubLayer, compLayer, mapId, cId, zMin) {
    var name2selection = {};
    var name2popup = {};
    var specific_names = [];

    var result=[false];
    var specificJson = getFilteredJson(map, json_data, name2popup, specific_names, name2selection, z, mapId, zMin, result,
        function (feature) {
            return !feature.properties.ubiquitous && matchesLevel(z, feature) && matchesCompartment(cId, feature);
        }
    );
    var ubiquitousJson = getFilteredJson(map, json_data, name2popup, specific_names, name2selection, z, mapId, zMin, result,
        function (feature) {
            return feature.properties.ubiquitous && matchesLevel(z, feature) && matchesCompartment(cId, feature);
        }
    );
    if (!result[0]) {
        return false;
    }

    var all_names = Object.keys(name2popup);

    z = rescaleZoom(zMin, z);

    if (map.getZoom() == z) {
        compLayer.addLayer(specificJson);
        ubLayer.addLayer(ubiquitousJson);
        setAutocomplete(map, map.hasLayer(ubLayer) ? all_names : specific_names, name2popup);
    }

    map.on('zoomend', function (e) {
        var zoom = map.getZoom();
        // if we are about to zoom in/out to this geojson
        if (zoom == z) {
            compLayer.addLayer(specificJson);
            ubLayer.addLayer(ubiquitousJson);
            setAutocomplete(map, map.hasLayer(ubLayer) ? all_names : specific_names, name2popup);
        } else {
            if (compLayer.hasLayer(specificJson)) {
                compLayer.removeLayer(specificJson);
                ubLayer.removeLayer(ubiquitousJson);
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