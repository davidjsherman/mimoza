/**
 * Created by anna on 4/4/14.
 */

function formatGA(ga) {
    var ga_res = '';
    if (ga) {
        var or_closes = ga.split('&');
        ga_res = '<table border="0"><tr class="centre"><th colspan="' + (2 * or_closes.length - 1) + '"  class="centre">Gene association</th></tr><tr>';
        for (var i = 0, len = or_closes.length; i < len; i++) {
            var or_close = or_closes[i];
            ga_res += '<td><table border="0">';
            var genes = or_close.split('|');
            if (genes.length > 1) {
                ga_res += "<tr></tr><td class='centre'><i>(or)</i></td></tr>";
            }
            for (var j = 0, jlen = genes.length; j < jlen; j++) {
                ga_res += "<tr><td><a href=\'http://www.ncbi.nlm.nih.gov/gene/?term=" + genes[j] + "[sym]\' target=\'_blank\'>" + genes[j] + '</a></td></tr>';
            }
            ga_res += '</table></td>';
            if (i < len - 1) {
                ga_res += '<td class="centre"><i>and</i></td>'
            }
        }
        ga_res += '</tr></table>';
    }
    return ga_res
}

function formatFormula(reversible, reactants, products) {
    reactants = reactants.split('&');
    products = products.split('&');
    var res = '<table border="0"><tr>';

    res += '<td><table border="0">';
    for (var i = 0, len = reactants.length; i < len; i++) {
        sv = reactants[i].split(' * ');
        res += '<tr><td>' + sv[0] + '&nbsp;</td><td>' + sv[1] + '</td></tr>';
    }
    res += '</table></td>';

    if (reversible) {
        res += '<th class="centre">&#8596;</th>';
    } else {
        res += '<th class="centre">&#65515;</th>';
    }

    res += '<td><table border="0">';
    for (i = 0, len = products.length; i < len; i++) {
        sv = products[i].split(' * ');
        res += '<tr><td>' + sv[0] + '&nbsp;</td><td>' + sv[1] + '</td></tr>';
    }
    res += '</table></td>';

    res += '</tr></table>';
    return res
}

function formatChebi(ch) {
    if (ch && ch.toUpperCase().indexOf("UNKNOWN") == -1) {
        return "<a href=\'http://www.ebi.ac.uk/chebi/searchId.do?chebiId=" + ch.toUpperCase() + "\' target=\'_blank\'>" + ch.toUpperCase() + "</a>";
    }
    return "";
}

function formatGo(term) {
    if (term) {
        return "<a href=\'http://www.ebi.ac.uk/QuickGO/GTerm?id=" + term.toUpperCase() + "\' target=\'_blank\'>" + term.toUpperCase() + "</a>";
    }
    return "";
}

function formatLink(c_id) {
    if (c_id) {
        return "<a href=\'?name=" + c_id + "\'>Go inside</a>";
    }
    return "";
}

function getBounds(feature, map) {
    var e = feature.geometry.coordinates;
    var w = feature.properties.w / 2;
    var h = feature.properties.h / 2;
    var x = e[0], y = e[1];
    var southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1);
    return new L.LatLngBounds(southWest, northEast);
}

function p(text) {
    return "<p class='popup centre'>" + text + "</p>";
}

function i(text) {
    return "<span class='explanation'>" + text + "</span>";
}

function h2(text) {
    return "<h2>" + text + "</h2>";
}

function addPopups(map, name2popup, specific_names, name2selection, feature, layer, mapId, zoom) {
    if (EDGE == feature.properties.type) {
        return;
    }
    var w = feature.properties.w / 2;
    var h = feature.properties.h / 2;
    var scaleFactor = Math.pow(2, zoom);
    var r = Math.min(w, h) * scaleFactor;
    var big_enough = r > 10;
    if (!big_enough) {
        return;
    }
    var content = h2(feature.properties.name) + p(i("id: ") + feature.properties.id);
    var label = content;
    if (REACTION == feature.properties.type) {
        var transport = feature.properties.transport ? p(i("Is a transport reaction.")) : "";
        var ga_res = p(formatGA(feature.properties.gene_association));
        var formula = p(formatFormula(feature.properties.reversible,
            feature.properties.reactants, feature.properties.products));
        content += formula + ga_res + transport;
        label += formula + transport;
    } else if (SPECIES == feature.properties.type) {
        var transported = feature.properties.transport ? p(i("Participates in a transport reaction.")) : "";
        var ch = p(formatChebi(feature.properties.term));
        var compartment = p(i("compartment: ") + feature.properties.compartment);
        content += compartment + ch + transported;
        label += compartment + transported;
    } else if (COMPARTMENT == feature.properties.type) {
//        var link = p(formatLink(feature.properties.id));log
        content += p(formatGo(feature.properties.term)); // + link;
    }
    var bounds = getBounds(feature, map);
    var size = $('#' + mapId).height();
    var popup = L.popup({autoPan: true, keepInView: true, maxWidth: size - 2, maxHeight: size - 2, autoPanPadding: [1, 1]}).setContent(content).setLatLng(bounds.getCenter());
    if (feature.properties.ubiquitous) {
        if (!name2selection.hasOwnProperty(feature.properties.id)) {
            name2selection[feature.properties.id] = L.featureGroup();
        }
        var selection_layer = name2selection[feature.properties.id];
        selection_layer.addLayer(highlightCircle(feature, map, zoom));
        map.on('popupopen', function(e) {
            if (e.popup == popup) {
                map.addLayer(selection_layer);
            }
        });
        map.on('popupclose', function(e) {
            if (e.popup == popup) {
                map.removeLayer(selection_layer);
            }
        });
    }
    layer.bindLabel(label).bindPopup(popup);
    [feature.properties.name, feature.properties.label, feature.properties.id, feature.properties.term].forEach(function (key) {
        if (key) {
            name2popup[key] = popup;
            if (!feature.properties.ubiquitous) {
                specific_names.push(key);
            }
        }
    });

}

function highlightCircle(feature, map, zoom) {
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
    };
    var e = feature.geometry.coordinates;
    var x = e[0], y = e[1];
    var w = feature.properties.w / 2;
    var h = feature.properties.h / 2;
    var centre = map.unproject([x, y], 1);
    var scaleFactor = Math.pow(2, zoom);
    var r = Math.min(w, h) * scaleFactor;
    node = L.circleMarker(centre, props);
    node.setRadius(r/2);
    return node;
}

function search(map, name2popup) {
    var srch = document.search_form.search_input.value;
    if (srch && name2popup.hasOwnProperty(srch)) {
        name2popup[srch].openOn(map);
    }
}

function add(map, key, value) {
    if (map.hasOwnProperty(key)) {
        map[key].push(value);
    } else {
        map[key] = [value];
    }
}