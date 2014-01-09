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
//    res += '<tr><td><table border="0"><tr><th colspan="2">Reactants</th></tr>';
    res += '<tr><td><table border="0"><tr><th>Reactants</th></tr>';
    for (var i = 0, len = reactants.length; i < len; i++) {
        sv = reactants[i].split(' * ');
//        res += '<tr><td>' + sv[0] + '</td><td>' + sv[1] + '</td></tr>';
        res += '<tr><td>' + sv[1] + '</td></tr>';
    }
    res += '</table></td>';
    if (reversible) {
        res += '<th class="centre">&lt;-&gt;</th>';
    } else {
        res += '<th class="centre">-&gt;</th>';
    }
//    res += '<td><table border="0"><tr><th colspan="2">Products</th></tr>';
    res += '<td><table border="0"><tr><th>Products</th></tr>';
    for (i = 0, len = products.length; i < len; i++) {
        sv = products[i].split(' * ');
//        res += '<tr><td>' + sv[0] + '</td><td>' + sv[1] + '</td></tr>';
        res += '<tr><td>' + sv[1] + '</td></tr>';
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

function formatLink(comp) {
    if (comp) {
        return "<a href=\'./compartment.html?name=" + comp + "\'>Go inside</a>";
    }
    return "";
}


function initializeMap(max_zoom) {
    var map = L.map('map', {
        maxZoom: max_zoom,
        minZoom: 2
        //crs: L.CRS.Simple
    });
    var southWest = map.unproject([0, 512], 1);
    var northEast = map.unproject([512, 0], 1);
    var bounds = new L.LatLngBounds(southWest, northEast);
    map.setView(bounds.getCenter(), 2);
    map.setMaxBounds(bounds);
    return map;
}

function pnt2layer(map, feature) {
    var e = feature.geometry.coordinates;
    var w = feature.properties.width / 2;
    var h = feature.properties.height / 2;
    var props = {
        name: feature.properties.name,
        color: feature.properties.bcolor,
        fillColor: feature.properties.color,
        fillOpacity: 1,
        opacity: 1,
        weight: 1,
        fill: true
    };
    if ('edge' == feature.properties.type) {
        props['weight'] = w * 2;
        props['lineCap'] = 'arrow';
        props['clickable'] = false;
        props['color'] = feature.properties.color;
        return L.polyline([map.unproject(e[0], 1), map.unproject(e[1], 1)], props);
    }
    var x = e[0], y = e[1];
    var southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1),
        bounds = new L.LatLngBounds(southWest, northEast);
    var r_x = map.unproject([x - w / 2, y], 1).distanceTo(map.unproject([x + w / 2, y], 1)),
        r_y = map.unproject([x, y + h/ 2], 1).distanceTo(map.unproject([x, y - h/2], 1));
    var r = (r_x + r_y) / 2;
    var centre = map.unproject(e, 1);
//    var centre = bounds.getCenter();
    if ('background' == feature.properties.type) {
        props['fillOpacity'] = 0.3;
        props['weight'] = 0;
        props['clickable'] = false;
        if (14 == feature.properties.shape) {
            var circle = L.circle(centre, r, props);
//            var circle = L.circleMarker(centre, props);
//            circle.setRadius(w * map.getZoom());
            return circle;
        } else {
            return  L.rectangle(bounds, props);
        }
    }
    var cl = ("species" == feature.properties.type) ? 'sticky round' : 'sticky';
    var label = L.marker(centre,
        {
            icon: L.divIcon({
                className: 'count-icon',
                html: '<div style="max-width:' + w * map.getZoom() * 2 +'";max-height:' + h * map.getZoom() * 2 + '"><p id="' + feature.properties.id + '" class="fittext">' + feature.properties.name + '</p></div>', //'<span class="' + cl + '">' + feature.properties.name + '</span>',
                iconSize: [w * map.getZoom() * 2, h * map.getZoom() * 2]
            })
        }
    );
    if ('reaction' == feature.properties.type || 'compartment' == feature.properties.type) {
        var rect = L.rectangle(bounds, props);
        return L.featureGroup([rect, label]);
    }
    if ('species' == feature.properties.type) {
        r = southWest.distanceTo(northEast) / (2 * Math.sqrt(2));
        var circle = L.circle(centre, r, props);
//        return circle;
        return L.featureGroup([label, circle]);
    }
    return null;
}

function addPopups(map, name2popup, feature, layer) {
    var content = '';
    if ('reaction' == feature.properties.type) {
        var ga_res = formatGA(feature.properties.gene_association);
        var formula = formatFormula(feature.properties.reversible, feature.properties.reactants, feature.properties.products);
        content = '<h2><b>' + feature.properties.name + "</h2><p class='popup'>" + formula + '</p><p class="popup">'+ ga_res + "</p>";
    } else if ('species' == feature.properties.type) {
        var ch = formatChebi(feature.properties.chebi);
        content = '<h2>' + feature.properties.name + "</h2><p>" + ch + "</p>";
    } else if ('compartment' == feature.properties.type) {
        var link = formatLink(feature.properties.name);
        content = '<h2>' + feature.properties.name + "</h2><p>" + link + "</p>";
    }
    if ('edge' == feature.properties.type) {
        return
    }
    var popup = L.popup({autoPan: true, keepInView:true, maxWidth:1020}).setContent(content);
    layer.bindPopup(popup); //.bindLabel('<i>' + feature.properties.name + '</i>', {noHide: true});
    name2popup[feature.properties.name.toLowerCase()] = popup;
}


function getGeoJson(map, json, name2popup) {
    if (json == null || json.length == 0){
        // pass
    } else if (json.length == 1) {
        getSimpleJson(map, json[0], name2popup);
    } else {
        getComplexJson(map, json[0], json[1], name2popup);
    }
}



function getComplexJson(map, json_zo, json_zi, name2popup) {
    var geojsonLayer = getSimpleJson(map, json_zo, name2popup);

//    var zo = true;
    map.on('zoomend', function (e) {
        if (map.getZoom() >= 3) {
//            if (zo) {
                geojsonLayer = getJson(map, json_zi, name2popup, geojsonLayer);
//                zo = false;
//            }
        } else if (map.getZoom() <= 2) {
//            if (!zo) {
                geojsonLayer = getJson(map, json_zo, name2popup, geojsonLayer);
//                zo = true;
//            }
        }
    });
}

function getSimpleJson(map, jsn, name2popup) {
    var jsn = L.geoJson(jsn, {
        pointToLayer: function(feature, latlng) {
            return pnt2layer(map, feature);
        },
        onEachFeature: function(feature, layer) {
            addPopups(map, name2popup, feature, layer);
        }
    }).addTo(map);
    var elements = document.getElementsByClassName('fittext');
    for (var i = 0; i < elements.length; i++) {
        fitText(elements[i], 0.6);
    }
    return jsn;
}

function getJson(map, jsn, name2popup, geojsonLayer) {
    for (var prop in name2popup) {
        if (name2popup.hasOwnProperty(prop)) {
            delete name2popup[prop];
        }
    }
    map.removeLayer(geojsonLayer);
    return getSimpleJson(map, jsn, name2popup);
}

function search(map, name2popup) {
    var srch = document.search_form.search_input.value.toLowerCase();
    if (srch && name2popup[srch]){
        name2popup[srch].openOn(map);
    }
}

function gup (name) {
    name = new RegExp('[?&]' + name.replace (/([[\]])/, '\\$1') + '=([^&#]*)');
    return (window.location.href.match(name) || ['', ''])[1];
}

function centerMap() {
    map.setView([0, 0], map.getZoom());
}