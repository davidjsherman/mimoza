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

function pnt2layer(map, feature, zoom) {
    var e = feature.geometry.coordinates;
    var w = getSize(feature) / 2;
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

function matchesCompartment(cId, feature) {
    var outCompIds = feature.properties.c_outs ? feature.properties.c_outs.split(',') : [];
    return !cId || cId == feature.properties.c_id || outCompIds.indexOf(cId) > -1;
}

function matchesLevel(level, feature) {
    return level >= feature.properties.zoom_min && level <= feature.properties.zoom_max
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