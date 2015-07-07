/**
 * Created by anna on 6/17/14.
 */

var MARGIN = 156,
    MAP_DIMENSION_SIZE = 512,
    EDGE = 0,
    SPECIES = 1,
    COMPARTMENT = 3,
    REACTION = 2,
    BG_SPECIES = 4,
    BG_REACTION = 5,
    BG_COMPARTMENT = 6,
    BG = [BG_SPECIES, BG_REACTION, BG_COMPARTMENT],
    TRANSPORT = "transport to outside",
    INNER_TRANSPORT = "inside transport",
    MIN_LABEL_SIZE = 10,
    MAX_LABEL_SIZE = 16;

function pnt2layer(map, compLayer, ubLayer, feature, fromZoom, toZoom, coords, minZoom, cId,
                   popupW, popupH, name2popup, name2zoom, name2selection) {
    "use strict";
    var e = feature.geometry.coordinates,
        scaleFactor = Math.pow(2, fromZoom),
        w = feature.properties.w;
    if (EDGE == feature.properties.type) {
        var props = {
            color: feature.properties.color,
            opacity: 1,
            weight: Math.min(Math.min(w / 2, 10), 4),
            lineCap: 'round',
            lineJoin: 'round',
            clickable: false,
            fill: false,
            zIndexOffset: 0,
            riseOnHover: false
        };
        return L.polyline(e.map(function (coord) {
            return map.unproject(coord, 1);
        }), props);
    }
    if (SPECIES == feature.properties.type || BG_SPECIES == feature.properties.type) {
        w /= Math.sqrt(2);
    }
    var x = e[0], y = e[1],
        is_bg = -1 !== BG.indexOf(feature.properties.type),
        props = {
            name: feature.properties.name,
            title: feature.properties.name,
            alt: feature.properties.name,
            id: feature.properties.id,
            color: BG_COMPARTMENT != feature.properties.type ? 'white': feature.properties.color,
            fillColor: feature.properties.color,
            fillOpacity: BG_COMPARTMENT == feature.properties.type ? 0 : (is_bg ? 0.3: 1),
            opacity: 1,
            weight: BG_COMPARTMENT != feature.properties.type ? (is_bg ? 0: Math.min(1, w / 10 * scaleFactor)): 4,
            fill: true,
            clickable: !is_bg,
            zIndexOffset: is_bg ? 6 : 0,
            riseOnHover: !is_bg
        },
        h = (BG_COMPARTMENT == feature.properties.type || COMPARTMENT == feature.properties.type) ?
            feature.properties.h : w,
        bounds = new L.LatLngBounds(map.unproject([x - w, y + h], 1), map.unproject([x + w, y - h], 1)),
        centre = map.unproject([x, y], 1),
        ne = bounds.getNorthEast(),
        sw = bounds.getSouthWest(),
        r = w * 40075000 * Math.cos(centre.lat * (Math.PI / 180)) / Math.pow(2, minZoom + 8);
    if (BG_COMPARTMENT == feature.properties.type || COMPARTMENT == feature.properties.type) {
        if (coords[2] == null || (BG_COMPARTMENT == feature.properties.type && cId == feature.properties.c_id
            || COMPARTMENT == feature.properties.type && cId == feature.properties.id)) {
            coords[2] = centre;
        }
    }
    if (BG_REACTION == feature.properties.type) {
        return L.rectangle(bounds, props);
    }
    if (BG_SPECIES == feature.properties.type) {
        return L.circle(centre, r, props);
    }
    var node = null;
    if (REACTION == feature.properties.type || COMPARTMENT == feature.properties.type || BG_COMPARTMENT == feature.properties.type) {
        node = L.rectangle(bounds, props);
    } else if (SPECIES == feature.properties.type) {
        node = L.circle(centre, r, props);
    } else {
        return null;
    }
    coords[0][0] = coords[0][0] == null ? sw.lat : Math.min(coords[0][0], sw.lat);
    coords[0][1] = coords[0][1] == null ? sw.lng : Math.max(coords[0][1], sw.lng);
    coords[1][0] = coords[1][0] == null ? ne.lat : Math.max(coords[1][0], ne.lat);
    coords[1][1] = coords[1][1] == null ? ne.lng : Math.min(coords[1][1], ne.lng);

    var popup = undefined,
        label = undefined;

    function addSelectionCircles(key) {
        if (!name2selection.hasOwnProperty(key)) {
            name2selection[key] = L.featureGroup();
        }
        var selection_layer = name2selection[key];
        selection_layer.addLayer(highlightCircle(centre, r));
        map.on('popupopen', function (e) {
            if (e.popup === popup) {
                if (map.hasLayer(ubLayer)) {
                    compLayer.addLayer(selection_layer);
                }
            }
        });
        map.on('popupclose', function (e) {
            if (e.popup === popup) {
                compLayer.removeLayer(selection_layer);
            }
        });
    }

    if (BG_COMPARTMENT != feature.properties.type) {
        popup = getPopup(feature, popupW, popupH);
        popup.setLatLng(centre);
        node.bindPopup(popup);
        if (SPECIES == feature.properties.type) {
            addSelectionCircles(feature.properties.id);
        }
        [feature.properties.name, feature.properties.id, feature.properties.t].forEach(function (key) {
            if (key) {
                if (!name2popup.hasOwnProperty(key)) {
                    name2popup[key] = popup;
                }
                if (!name2zoom.hasOwnProperty(key)) {
                    name2zoom[key] = [fromZoom, toZoom];
                }
            }
        });
        label = getLabel(feature);
        node.bindLabel(label, {direction: "auto", opacity: 1});
    }

    node = L.featureGroup([node]);
    var z2label = {},
        wz = null,
        sz = null;
    for (var z = fromZoom; z <= toZoom; z ++) {
        if (sz == null) {
            var scale = Math.pow(2, z);
            sz = h * scale;
            wz = w * scale;
        } else {
            sz *= 2;
            wz *= 2;
        }
        if (sz >= MIN_LABEL_SIZE) {
            var size = Math.min(Math.max(Math.round(sz / 2), MIN_LABEL_SIZE), MAX_LABEL_SIZE);
            var marker = L.marker(centre,
                {
                    icon: L.divIcon({
                        className: 'element-label',
                        html: "<span style=\"font-size:" + size +
                        "px;line-height:" + (size + 1) + "px;color:" +
                        (BG_COMPARTMENT == feature.properties.type ? feature.properties.color : "black") + "\">"
                        + (REACTION == feature.properties.type ? feature.properties.id : feature.properties.name) + "</span>",
                        iconSize: [wz, sz - sz % (size + 1)],
                        zIndexOffset: 0,
                        riseOnHover: false,
                        riseOffset: 0
                    })
                }
            );
            if (popup != undefined) {
                marker.bindPopup(popup);
            }
            if (label != undefined) {
                marker.bindLabel(label, {direction: "auto", opacity: 1});
            }
            z2label[z] = marker;
            if (size == 14) {
                for (var zz = z + 1; zz <= toZoom; zz++) {
                    z2label[zz] = marker;
                }
                break;
            }
        }
    }
    if (typeof map.getZoom() !== 'undefined') {
        if (z2label.hasOwnProperty(map.getZoom())) {
            node.addLayer(z2label[map.getZoom()]);
        }
    } else if (z2label.hasOwnProperty(fromZoom)) {
        node.addLayer(z2label[fromZoom]);
    }
    if (popup != undefined) {
        node.bindPopup(popup);
    }
    if (label != undefined) {
        node.bindLabel(label, {direction: "auto", opacity: 1});
    }
    map.on('zoomend', function (e) {
        for (z in z2label) {
            node.removeLayer(z2label[z]);
        }
        z = map.getZoom();
        if (z2label.hasOwnProperty(z)) {
            node.addLayer(z2label[z]);
        }
    });

    if (COMPARTMENT == feature.properties.type) {
        map.on('zoomend', function (e) {
            var mapBounds = map.getBounds();
            if (map.getZoom() > minZoom + 2 && map.getBounds().intersects(bounds) && (map.getZoom() == map.getMaxZoom()
            || bounds.contains(mapBounds.getSouthWest()) && bounds.contains(mapBounds.getNorthEast()))) {
                    window.location.href = "?id=" + feature.properties.id;
            }
        });
    }
    return node;
}

function matchesCompartment(cId, feature) {
    "use strict";
    if (TRANSPORT === cId) {
        return typeof feature.properties.tr !== 'undefined' && feature.properties.tr
            && (typeof feature.properties.inner === 'undefined' || !feature.properties.inner);
    }
    if (INNER_TRANSPORT === cId) {
        return typeof feature.properties.tr !== 'undefined' && feature.properties.tr
            && (typeof feature.properties.inner !== 'undefined' && feature.properties.inner);
    }
    return (typeof feature.properties.tr === 'undefined' || !feature.properties.tr)
            && (typeof feature.properties.inner === 'undefined' || !feature.properties.inner);//cId === feature.properties.c_id || cId === feature.properties.id;
}

function getFilteredJson(map, compLayer, ubLayer, jsn, name2popup, name2zoom, fromZoom, toZoom, mapId, coords, minZoom,
                         cId, filterFunction) {
    "use strict";
    var name2selection = {},
        $map = $('#' + mapId),
        popupW = $map.width() - 2,
        popupH = $map.height() - 2;
    return L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, compLayer, ubLayer, feature, fromZoom, toZoom, coords, minZoom, cId, popupW, popupH,
                name2popup, name2zoom, name2selection);
        },
        filter: function (feature, layer) {
            return filterFunction(feature);
        },
        onEachFeature: function(feature, layer) {
            feature.layer = layer;
        }
    });
}

function loadGeoJson(map, json, fromZoom, toZoom, ubLayer, compLayer, mapId, cId, name2popup, name2zoom, coords, minZoom, inZoom) {
    "use strict";
    var specificJson = getFilteredJson(map, compLayer, ubLayer, json, name2popup, name2zoom, fromZoom, toZoom, mapId,
            coords, minZoom, inZoom == null ? cId: inZoom,
            function (feature) {
                return (typeof feature.properties.ub === 'undefined' || !feature.properties.ub) && matchesCompartment(cId, feature);
            }
        ),
        ubiquitousJson = getFilteredJson(map, compLayer, ubLayer, json, name2popup, name2zoom, fromZoom, toZoom, mapId,
            coords, minZoom, inZoom == null ? cId: inZoom,
            function (feature) {
                return (typeof feature.properties.ub !== 'undefined' && feature.properties.ub)
                    && matchesCompartment(cId, feature);
            }
        );
    if (typeof map.getZoom() === 'undefined' && fromZoom <= minZoom && minZoom <= toZoom
        || fromZoom <= map.getZoom() && map.getZoom() <= toZoom) {
        compLayer.addLayer(specificJson);
        if (map.hasLayer(ubLayer)) {
            compLayer.addLayer(ubiquitousJson);
        }
    }
    if (fromZoom > minZoom || toZoom < map.getMaxZoom()) {
        map.on('zoomend', function (e) {
            // if we are about to zoom in/out to this geojson
            if (fromZoom <= map.getZoom() && map.getZoom() <= toZoom) {
                compLayer.addLayer(specificJson);
                if (map.hasLayer(ubLayer)) {
                    compLayer.addLayer(ubiquitousJson);
                }
            } else {
                compLayer.removeLayer(specificJson);
                compLayer.removeLayer(ubiquitousJson);
            }
        });
    }
    map.on('overlayadd', function(e) {
        if (e.layer === ubLayer && (fromZoom <= map.getZoom() && map.getZoom() <= toZoom)) {
            compLayer.addLayer(ubiquitousJson);
        }
    });
    map.on('overlayremove', function(e) {
        if (e.layer === ubLayer && (fromZoom <= map.getZoom() && map.getZoom() <= toZoom)) {
            compLayer.removeLayer(ubiquitousJson);
        }
    });
    return [specificJson.getLayers().length > 0, ubiquitousJson.getLayers().length > 0];
}
