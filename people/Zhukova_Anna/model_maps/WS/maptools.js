/**
 * Created by anna on 12/12/13.
 */

function formatGA(ga) {
    var ga_res = '';
    if (ga) {
        var or_closes = ga.split('&');
        ga_res = '<table border="0"><tr><th colspan="' + or_closes.length + '">Gene association</th></tr><tr>';
        for (i = 0, len = or_closes.length; i < len; i++) {
            var or_close = or_closes[i];
            ga_res += '<td><table border="0">';
            var genes = or_close.split('|');
            if (genes.length > 1) {
                ga_res += "<tr></tr><td class='centre'><i>(or)</i></td></tr>";
            }
            for (var j = 0, jlen = genes.length; j < jlen; j++) {
                ga_res += "<tr><td><a href=\'http://genolevures.org/elt/YALI/" + genes[j]+ "\' target=\'_blank\'>" + genes[j] + '</a></td></tr>';
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
    res += '<tr><td><table border="0"><tr><th colspan="2">Reactants</th></tr>';
    for (var i = 0, len = reactants.length; i < len; i++) {
        sv = reactants[i].split(' * ');
        res += '<tr><td>' + sv[0] + '</td><td>' + sv[1] + '</td></tr>';
    }
    res += '</table></td>';
    if (reversible) {
        res += '<th class="centre">&lt;-&gt;</th>';
    } else {
        res += '<th class="centre">-&gt;</th>';
    }
    res += '<td><table border="0"><tr><th colspan="2">Products</th></tr>';
    for (i = 0, len = products.length; i < len; i++) {
        sv = products[i].split(' * ');
        res += '<tr><td>' + sv[0] + '</td><td>' + sv[1] + '</td></tr>';
    }
    res += '</table></td></tr>';
    res += '</tr></table>';
    return res
}


function formatChebi(ch) {
    if (ch && ch.toUpperCase().indexOf("UNKNOWN") == -1) {
        return "<a href=\'http://www.ebi.ac.uk/chebi/searchId.do?chebiId=" + ch.toUpperCase() + "\' target=\'_blank\'>" + ch.toUpperCase() + "</a>";
    }
    return "";
}


function initializeMap(json_zo, json_zi, name2popup) {
    var map = L.map('map', {
        maxZoom: 4,
        minZoom: 2,
        crs: L.CRS.Simple
    }).setView([0, 0], 2);
    var southWest = map.unproject([0, 4096], 4);
    var northEast = map.unproject([4096, 0], 4);
    map.setMaxBounds(new L.LatLngBounds(southWest, northEast));

    getJson(map, json_zo, name2popup);

    var zo = true;
    map.on('zoomend', function (e) {
        var style = document.getElementById('map').style;
        if (map.getZoom() >= 3) {
            if (zo) {
                getJson(map, json_zi, name2popup);
                zo = false;
            }
        } else if (map.getZoom() <= 2) {
            if (!zo) {
                getJson(map, json_zo, name2popup);
                zo = true;
            }
        }
    });
    return map;
}

function getJson(map, jsn, name2popup) {
    try {
        for (var prop in name2popup) {
            if (name2popup.hasOwnProperty(prop)) {
                delete name2popup[prop];
            }
        }
        map.removeLayer(geojsonLayer);
    } catch (err) {
    }
    geojsonLayer = L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            var e = feature.geometry.coordinates;
            var col = feature.properties.color;
            var x = e[0], y = e[1];
            var r = feature.properties.radius / 2;
            var southWest = map.unproject([x - r, y + r], 1),
                northEast = map.unproject([x + r, y - r], 1),
                bounds = new L.LatLngBounds(southWest, northEast);
            return L.rectangle(bounds, {
                color: feature.properties.color,
                fillColor: feature.properties.color,
                fillOpacity: 0,
                opacity: 1,
                weight: 0
            });
        },
        onEachFeature: function (feature, layer) {
            var content = '';
            if ('reaction' == feature.properties.type) {
                var ga_res = formatGA(feature.properties.gene_association);
                var formula = formatFormula(feature.properties.reversible, feature.properties.reactants, feature.properties.products);
                content = '<h2><b>' + feature.properties.name + "</h2><p class='popup'>" + formula + '</p><p class="popup">'+ ga_res + "</p>";
            } else {
                var ch = formatChebi(feature.properties.chebi);
                content = '<h2>' + feature.properties.name + "</h2><p>" + ch + "</p>";
            }
            var popup = L.popup({autoPan: true, keepInView:true, maxWidth:1020}).setContent(content).setLatLng(map.unproject(feature.geometry.coordinates, 1));
            layer.bindPopup(popup);
            name2popup[feature.properties.name.toLowerCase()] = popup;
        }
    });
    geojsonLayer.addTo(map);
    return name2popup;
}

function search(map, name2popup) {
    var srch = document.search_form.search_input.value.toLowerCase();
    if (srch && name2popup[srch]){
        name2popup[srch].openOn(map);
    }
}
