/**
 * Created by anna on 4/4/14.
 */

function formatGA(ga) {
    var ga_res = '';
    if (ga) {
        var or_closes = ga.split('&');
        ga_res = '<table border="0"><tr class="centre"><th colspan="' + (2 * or_closes.length - 1) + '"  class="centre">Gene association</th></tr><tr>';
        for (i = 0, len = or_closes.length; i < len; i++) {
            var or_close = or_closes[i];
            ga_res += '<td><table border="0">';
            var genes = or_close.split('|');
            if (genes.length > 1) {
                ga_res += "<tr></tr><td class='centre'><i>(or)</i></td></tr>";
            }
            for (var j = 0, jlen = genes.length; j < jlen; j++) {
                ga_res += "<tr><td><a href=\'http://genolevures.org/elt/YALI/" + genes[j] + "\' target=\'_blank\'>" + genes[j] + '</a></td></tr>';
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

function formatLink(comp) {
    if (comp) {
        return "<a href=\'?name=" + comp.toLowerCase().replace(' ', '_') + "\'>Go inside</a>";
    }
    return "";
}

function getBounds(feature, map) {
    var e = feature.geometry.coordinates;
    var w = feature.properties.width / 2;
    var h = feature.properties.height / 2;
    var x = e[0], y = e[1];
    var southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1);
    return new L.LatLngBounds(southWest, northEast);
}

function closePopups(openPopups, map) {
    openPopups.eachLayer(function (lr) {
        map.removeLayer(lr);
    });
    openPopups.clearLayers();
}
function addPopups(map, name2popup, name2selection, feature, layer) {
    var content = '';
    var label = '';
    if (REACTION == feature.properties.type) {
        var transport = feature.properties.transport ? "<p class='popup centre'>Is a transport reaction.</p>" : "";
        var ga_res = formatGA(feature.properties.gene_association);
        var formula = formatFormula(feature.properties.reversible, feature.properties.reactants, feature.properties.products);
        content = '<h2>' + feature.properties.name + "</h2><p class='popup centre'><i>id: </i>" + feature.properties.id + "</p><p class='popup centre'>" + formula + '</p><p class="popup centre">' + ga_res + "</p>" + transport;
        label = '<h2>' + feature.properties.name + "</h2><p class='popup centre'><i>id: </i>" + feature.properties.id + "</p><p class='popup centre'>" + formula + '</p>' + transport;
    } else if (SPECIES == feature.properties.type) {
        var transport = feature.properties.transport ? "<p class='popup centre'>Participates in a transport reaction.</p>" : ""
        var ch = formatChebi(feature.properties.term);
        content = '<h2>' + feature.properties.name + "</h2><p class='popup centre'><i>id: </i>" + feature.properties.id + "</p><p class='popup centre'>" + ch + "</p>" + transport;
        label = '<h2>' + feature.properties.name + "</h2><p class='popup centre'><i>id: </i>" + feature.properties.id + "</p>" + transport;
    } else if (COMPARTMENT == feature.properties.type) {
        var link = formatLink(feature.properties.name);
        var go_term = formatGo(feature.properties.term);
        content = '<h2>' + feature.properties.name + "</h2><p class='popup centre'><i>id: </i>" + feature.properties.id + "</p><p class='popup centre'>" + go_term + "</p><p class='popup centre'>" + link + "</p>";
        label = '<h2>' + feature.properties.name + "</h2><p class='popup centre'><i>id: </i>" + feature.properties.id + "</p>";
    }
    if (EDGE == feature.properties.type) {
        return;
    }
    var bounds = getBounds(feature, map);
    var size = $('#map').height();
    var popup = L.popup({autoPan: true, keepInView: true, maxWidth: size - 2, maxHeight: size - 2, autoPanPadding: [1, 1]}).setContent(content).setLatLng(bounds.getCenter());
    if (feature.properties.ubiquitous) {
        if (!name2selection.hasOwnProperty(feature.properties.id)) {
            name2selection[feature.properties.id] = L.featureGroup();
        }
        var selection_layer = name2selection[feature.properties.id];
        selection_layer.addLayer(highlightCircle(feature, map));
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
    [feature.properties.name, feature.properties.label, feature.properties.id, feature.properties.chebi].forEach(function (key) {
        if (key) {
            name2popup[key] = popup;
        }
    });

}

function highlightCircle(feature, map) {
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
    var w = feature.properties.width / 2;
    var h = feature.properties.height / 2;
    var southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1),
        bounds = new L.LatLngBounds(southWest, northEast);
    var d = southWest.distanceTo(northEast);
    var centre = bounds.getCenter();
    return L.circle(centre, d / 2, props);
}

function search(map, name2popup) {
//    closePopups(openPopups, map);
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