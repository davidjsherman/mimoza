/**
 * Created by anna on 4/4/14.
 */

function formatGA(ga) {
    "use strict";
    var ga_res = '',
        or_closes,
        i,
        j,
        genes;
    if (ga) {
        or_closes = ga.split('&');
        ga_res = '<table border="0"><tr class="centre"><th colspan="' + (2 * or_closes.length - 1) + '"  class="centre">Gene association</th></tr><tr>';
        for (i = 0; i < or_closes.length; i += 1) {
            genes = or_closes[i].split('|');
            ga_res += '<td><table border="0">';
            if (genes.length > 1) {
                ga_res += "<tr></tr><td class='centre'><i>(or)</i></td></tr>";
            }
            for (j = 0; j < genes.length; j += 1) {
                ga_res += "<tr><td><a href=\'http://www.ncbi.nlm.nih.gov/gene/?term=" + genes[j] + "[sym]\' target=\'_blank\'>" + genes[j] + '</a></td></tr>';
            }
            ga_res += '</table></td>';
            if (i < or_closes.length - 1) {
                ga_res += '<td class="centre"><i>and</i></td>';
            }
        }
        ga_res += '</tr></table>';
    }
    return ga_res;
}

function formatFormula(reversible, reactants, products) {
    "use strict";
    reactants = reactants.split('&');
    products = products.split('&');
    var res = '<table border="0"><tr><td><table border="0">',
        i,
        sv;
    for (i = 0; i < reactants.length; i += 1) {
        sv = reactants[i].split(' * ');
        if (sv) {
            res += '<tr><td>' + sv[0] + '&nbsp;</td><td>' + sv[1] + '</td></tr>';
        }
    }
    res += '</table></td>';
    if (reversible) {
        res += '<th class="centre">&#8596;</th>';
    } else {
        res += '<th class="centre">&#65515;</th>';
    }
    res += '<td><table border="0">';
    for (i = 0; i < products.length; i += 1) {
        sv = products[i].split(' * ');
        if (sv) {
            res += '<tr><td>' + sv[0] + '&nbsp;</td><td>' + sv[1] + '</td></tr>';
        }
    }
    res += '</table></td></tr></table>';
    return res;
}

function formatChebi(ch) {
    "use strict";
    if (ch && ch.toUpperCase().indexOf("UNKNOWN") === -1) {
        return "<a href=\'http://www.ebi.ac.uk/chebi/searchId.do?chebiId=" + ch.toUpperCase() + "\' target=\'_blank\'>" + ch.toUpperCase() + "</a>";
    }
    return "";
}

function formatGo(term) {
    "use strict";
    if (term) {
        return "<a href=\'http://www.ebi.ac.uk/QuickGO/GTerm?id=" + term.toUpperCase() + "\' target=\'_blank\'>" + term.toUpperCase() + "</a>";
    }
    return "";
}

function getBounds(feature, map) {
    "use strict";
    var e = feature.geometry.coordinates,
        w = feature.properties.w / 2,
        h = feature.properties.h / 2,
        x = e[0],
        y = e[1],
        southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1);
    return new L.LatLngBounds(southWest, northEast);
}

function p(text) {
    "use strict";
    return "<p class='popup centre'>" + text + "</p>";
}

function i(text) {
    "use strict";
    return "<span class='explanation'>" + text + "</span>";
}

function addPopups(map, name2popup, name2zoom, name2selection, feature, layer, mapId, zoom, realZoom) {
    "use strict";
    if (EDGE == feature.properties.type) {
        return;
    }
    var scaleFactor = Math.pow(2, zoom),
        r = Math.min(feature.properties.w / 2, feature.properties.h / 2) * scaleFactor,
        content = "<h2>" + feature.properties.name + "</h2>" + p(i("id: ") + feature.properties.id),
        label = content;
    if (r <= MIN_CLICKABLE_R) {
        return;
    }
    if (REACTION == feature.properties.type) {
        var transport = feature.properties.transport ? p(i("Is a transport reaction.")) : "",
            ga_res = p(formatGA(feature.properties.gene_association)),
            formula = p(formatFormula(feature.properties.reversible, feature.properties.reactants, feature.properties.products));
        content += formula + ga_res + transport;
        label += formula + transport;
    } else if (SPECIES == feature.properties.type) {
        var transported = feature.properties.transport ? p(i("Participates in a transport reaction.")) : "",
            ch = p(formatChebi(feature.properties.term)),
            compartment = p(i("compartment: ") + feature.properties.compartment);
        content += compartment + ch + transported;
        label += compartment + transported;
    } else if (COMPARTMENT == feature.properties.type) {
        content += p(formatGo(feature.properties.term)); // + link;
    }
    var bounds = getBounds(feature, map),
        size = $('#' + mapId).height(),
        popup = L.popup({
            autoPan: true,
            keepInView: true,
            maxWidth: size - 2,
            maxHeight: size - 2,
            autoPanPadding: [1, 1]
        }).setContent(content).setLatLng(bounds.getCenter());
    if (feature.properties.ubiquitous) {
        var key = feature.properties.id;
        if (!name2selection.hasOwnProperty(key)) {
            name2selection[key] = L.featureGroup();
        }
        var selection_layer = name2selection[key];
        selection_layer.addLayer(highlightCircle(feature, map, zoom));
        map.on('popupopen', function(e) {
            if (e.popup === popup) {
                map.addLayer(selection_layer);
            }
        });
        map.on('popupclose', function(e) {
            if (e.popup === popup) {
                map.removeLayer(selection_layer);
            }
        });
        map.on('zoomstart', function(e) {
            if (map.hasLayer(selection_layer)) {
                map.removeLayer(selection_layer);
                map.closePopup(popup);
            }
        });
    }
    layer.bindLabel(label).bindPopup(popup);
    [feature.properties.name, feature.properties.label, feature.properties.id, feature.properties.term].forEach(function (key) {
        if (key) {
            name2popup[key] = popup;
            if (!name2zoom.hasOwnProperty(key)) {
                name2zoom[key] = [zoom];
            } else if (name2zoom[key].indexOf(realZoom) === -1){
                name2zoom[key].push(realZoom);
            }
        }
    });

}

function highlightCircle(feature, map, zoom) {
    "use strict";
    var props = {
            name: feature.properties.name,
            title: feature.properties.name,
            alt: feature.properties.name,
            id: feature.properties.id,
            color: "#ac3131",
            fillColor: "#ac3131",
            fillOpacity: 0.7,
            opacity: 1,
            lineCap: ROUND,
            lineJoin: ROUND,
            weight: 2,
            fill: true,
            clickable: false
        },
        e = feature.geometry.coordinates,
        centre = map.unproject([e[0], e[1]], 1),
        scaleFactor = Math.pow(2, zoom),
        r = Math.min(feature.properties.w / 2, feature.properties.h / 2) * scaleFactor,
        node = L.circleMarker(centre, props);
    node.setRadius(r / 2);
    return node;
}

function search(map, name2popup, name2zoom) {
    "use strict";
    var srch = document.search_form.search_input.value;
    if (srch && name2popup.hasOwnProperty(srch)) {
        var zoom = map.getZoom(),
            zooms = name2zoom[srch];
        if (zooms.indexOf(zoom) === -1) {
            var max_zoom = Math.max.apply(Math, zooms);
            if (zoom > max_zoom) {
                map.setZoom(max_zoom);
            } else {
                var min_zoom = Math.min.apply(Math, zooms);
                map.setZoom(min_zoom);
            }
        }
        name2popup[srch].openOn(map);
    }
}

function add(map, key, value) {
    "use strict";
    if (map.hasOwnProperty(key)) {
        map[key].push(value);
    } else {
        map[key] = [value];
    }
}