/**
 * Created by anna on 12/12/13.
 */

function formatLabel(feature, w, h) {
    var style = 'border:0px solid red; height:' + h + 'px; width:' + w + 'px; overflow:hidden; font-size:14px; line-height:auto;';
    return '<div class="fittext" style="' + style + '">' + feature.properties.name + '</div>';
}


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
//    res += '<tr><td><table border="0"><tr><th>Reactants</th></tr>';
    for (var i = 0, len = reactants.length; i < len; i++) {
        sv = reactants[i].split(' * ');
        res += '<tr><td>' + sv[0] + '</td><td>' + sv[1] + '</td></tr>';
//        res += '<tr><td>' + sv[1] + '</td></tr>';
    }
    res += '</table></td>';
    if (reversible) {
        res += '<th class="centre">&lt;-&gt;</th>';
    } else {
        res += '<th class="centre">-&gt;</th>';
    }
    res += '<td><table border="0"><tr><th colspan="2">Products</th></tr>';
//    res += '<td><table border="0"><tr><th>Products</th></tr>';
    for (i = 0, len = products.length; i < len; i++) {
        sv = products[i].split(' * ');
        res += '<tr><td>' + sv[0] + '</td><td>' + sv[1] + '</td></tr>';
//        res += '<tr><td>' + sv[1] + '</td></tr>';
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
        minZoom: 1
        //crs: L.CRS.Simple
    });
    var southWest = map.unproject([0, 512], 1);
    var northEast = map.unproject([512, 0], 1);
    var bounds = new L.LatLngBounds(southWest, northEast);
    map.setView(bounds.getCenter(), 2);
    map.setMaxBounds(bounds);
    return map;
}


function uproject(map, x, y, w, h) {
    var r_x = map.unproject([x - w / 2, y], 1).distanceTo(map.unproject([x + w / 2, y], 1)),
        r_y = map.unproject([x, y + h/ 2], 1).distanceTo(map.unproject([x, y - h/2], 1));
    return (r_x + r_y) / 2;
}


function pnt2layer(map, feature) {
    var e = feature.geometry.coordinates;
    var w = feature.properties.width / 2;
    var h = feature.properties.height / 2;
    if ('edge' == feature.properties.type) {
        return L.polyline([map.unproject(e[0], 1), map.unproject(e[1], 1)], {
            color: feature.properties.color,
            fillColor: feature.properties.color,
            fillOpacity: 1,
            opacity: 1,
            weight: map.getZoom() * w,
            lineCap: 'arrow',
            clickable: false,
            fill: true
        });
    }
    var props = {
        name: feature.properties.name,
        id: feature.properties.id,
        color: feature.properties.bcolor,
        fillColor: feature.properties.color,
        fillOpacity: 'background' == feature.properties.type ? 0.3 : 1,
        opacity: 1,
        weight: 'background' == feature.properties.type ? 0 : map.getZoom() / 2,
        fill: true,
        clickable: 'background' != feature.properties.type
    };
    var x = e[0], y = e[1];
    if (('species' == feature.properties.type) || ('background' == feature.properties.type) && (14 == feature.properties.shape)) {
        w /= Math.sqrt(2);
        h /= Math.sqrt(2);
    }
    var southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1),
        bounds = new L.LatLngBounds(southWest, northEast);
    var d = southWest.distanceTo(northEast);
//    var centre = map.unproject(e, 1);
    var centre = bounds.getCenter();
    if ('background' == feature.properties.type) {
        if (14 == feature.properties.shape) {
            return L.circle(centre, d / 1.8, props);
        } else {
            return  L.rectangle(bounds, props);
        }
    }
    var node = null;
    if ('reaction' == feature.properties.type || 'compartment' == feature.properties.type) {
        node = L.rectangle(bounds, props);
    }
    if ('species' == feature.properties.type) {
        node = L.circle(centre, d / 2, props);
    }
    if (node) { //&& w * map.getZoom() >= 10) {
        var label = L.marker(centre,
            {
                icon: L.divIcon({
                    className: 'count-icon',
                    html: formatLabel(feature, w * map.getZoom() * 2, h * map.getZoom() * 2),
                    iconSize: [w * map.getZoom() * 2, h * map.getZoom() * 2]
                })
            }
        );
        return L.featureGroup([node, label]);
    }
    return node;
}

function addPopups(name2popup, feature, layer) {
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
    fitLabels(map.getZoom(), map.getZoom());
}



function getComplexJson(map, json_zo, json_zi, name2popup) {
    var geojsonLayer = getSimpleJson(map, json_zo, name2popup);
    var zo = map.getZoom();
    map.on('zoomend', function (e) {
        if (map.getZoom() >= 3) {
            if (zo < 3) {
                geojsonLayer = getJson(map, json_zi, name2popup, geojsonLayer);
            }
        } else if (zo >= 3) {
                geojsonLayer = getJson(map, json_zo, name2popup, geojsonLayer);
        }
        fitLabels(map.getZoom(), zo);
        zo = map.getZoom();
    });
}

function fitLabels(zn, zo){
    console.log('fitting labels into nodes');
    $('.fittext', '#map').each(function(i, obj) {
        var old_height = $(this).height();
        var height = (old_height * zn) / zo;
        var old_width = $(this).width();
        var width = (old_width * zn) / zo;
        var size = Math.max(width / 5, 5);
        $(this).css({
            'height': height,
            'width': width,
            'font-size': size
        });
        var offset = $(this).offset();
        $(this).offset({ top: offset.top + (old_height - height) / 2, left: offset.left + (old_width - width) / 2});
//        if (width >= 12 && size > 6) {
//            $(this).wrapInner("<div class='wrap'></div>");
//            var $i = $(this).children('.wrap')[0];
//            while($i.scrollHeight > height && size > 6) {
//                size--;
//                $(this).css("font-size", size);
//            }
//        }
    });
//    $('.wrap').children().unwrap();
}

function getSimpleJson(map, jsn, name2popup) {
    return L.geoJson(jsn, {
        pointToLayer: function(feature, latlng) {
            return pnt2layer(map, feature);
        },
        onEachFeature: function(feature, layer) {
            addPopups(name2popup, feature, layer);
        }
    }).addTo(map);
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