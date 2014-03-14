/**
 * Created by anna on 12/12/13.
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

    res += '<td><table border="0">'; //<tr><th colspan="2">Reactants</th></tr>';
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

    res += '<td><table border="0">'; //<tr><th colspan="2">Products</th></tr>';
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
        return "<a href=\'./comp.html?name=" + comp.toLowerCase().replace(' ', '_') + "\'>Go inside</a>";
    }
    return "";
}

function adjustMapSize() {
    var dimention = Math.min($(window).height(), $(window).width());//screen.height, screen.width);
    var size = Math.max(256, Math.pow(2, Math.floor(Math.log(dimention) / Math.log(2))));
    var $map_div = $("#map");
    var old_width = $map_div.height();
    if (old_width != size) {
        $map_div.css({
            'height': size,
            'width': size
        });
        $(".leaflet-popup").css({
            "maxWidth": size,
            'maxHeight': size
        });
        $(".leaflet-popup-content").css({
            "maxWidth": size - 10,
            'maxHeight': size - 10
        });
    }
}

function initializeMap(max_zoom) {
    adjustMapSize();
    var margin = 156;
    var map = L.map('map', {
        maxZoom: max_zoom,
        minZoom: 0,
        attributionControl: false,
        padding: [156, 156]
    });
    var southWest = map.unproject([0 - margin, 512 + margin], 1);
    var northEast = map.unproject([512 + margin, 0 - margin], 1);
    var bounds = new L.LatLngBounds(southWest, northEast);
    map.setView(bounds.getCenter(), 1);
    map.setMaxBounds(bounds);
    var popup = null;
    map.on('popupopen', function (e) {
        console.log(e.popup);
        popup = e.popup;
    });
    map.on('dragstart', function (e) {
        if (popup) {
            console.log(e);
            map.closePopup(popup);
            popup.options['keepInView'] = false;
            map.openPopup(popup);
            popup.options['keepInView'] = true;
            popup = null;
        }
    });

    window.onresize = function (event) {
        adjustMapSize();
    };

    return map;
}


function uproject(map, x, y, w, h) {
    var r_x = map.unproject([x - w / 2, y], 1).distanceTo(map.unproject([x + w / 2, y], 1)),
        r_y = map.unproject([x, y + h / 2], 1).distanceTo(map.unproject([x, y - h / 2], 1));
    return (r_x + r_y) / 2;
}

var EDGE = 0;
var SPECIES = 1;
var COMPARTMENT = 3;
var REACTION = 2;
var BG = 4;


function pnt2layer(map, feature, edges) {
    var e = feature.geometry.coordinates;
    var w = feature.properties.width / 2;
    var h = feature.properties.height / 2;
    if (EDGE == feature.properties.type) {
        edges.addLayer(L.polyline(e.map(function (coord) {
            return map.unproject(coord, 1)
        }), {
            color: feature.properties.color,
            opacity: 1,
            weight: w * Math.pow(2, map.getZoom() - 1),
            lineCap: 'round',
            lineJoin: 'round',
            clickable: false,
            fill: false
        }));
        return edges;
    }
    var x = e[0], y = e[1];
    if ((SPECIES == feature.properties.type) || (BG == feature.properties.type) && (14 == feature.properties.shape)) {
        w /= Math.sqrt(2);
        h /= Math.sqrt(2);
    }
    var props = {
        name: feature.properties.name,
        title: feature.properties.name,
        alt: feature.properties.name,
        id: feature.properties.id,
        color: 'white', //feature.properties.border,
        fillColor: feature.properties.color,
        fillOpacity: BG == feature.properties.type ? 0.3 : 1,
        opacity: 1,
        lineCap: 'round',
        lineJoin: 'round',
        weight: BG == feature.properties.type ? 0 : w / 10 * Math.pow(2, map.getZoom() - 1),
        fill: true,
        clickable: BG != feature.properties.type
    };
    var southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1),
        bounds = new L.LatLngBounds(southWest, northEast);
    var d = southWest.distanceTo(northEast);
//    var centre = map.unproject(e, 1);
    var centre = bounds.getCenter();
    if (BG == feature.properties.type) {
        if (14 == feature.properties.shape) {
            return L.circle(centre, d / 1.8, props);
        } else {
            return  L.rectangle(bounds, props);
        }
    }
    var node = null;
    if (REACTION == feature.properties.type || COMPARTMENT == feature.properties.type) {
        node = L.rectangle(bounds, props);
    }
    if (SPECIES == feature.properties.type) {
        node = L.circle(centre, d / 2, props);
    }
    if (node && w * Math.pow(2, (map.getZoom() >= 3 ? map.getMaxZoom() : 3) - 1) >= 25) {
        var label = L.marker(centre,
            {
                icon: L.divIcon({
                    className: 'count-icon',
                    html: feature.properties.label,//formatLabel(feature, w * map.getZoom() * 2, h * map.getZoom() * 2),
                    iconSize: [w * Math.pow(2, map.getZoom() - 1) * 1.8, h * Math.pow(2, map.getZoom() - 1) * 1.8]
                })
            }
        );
        return L.featureGroup([node, label]);
    }
    return node;
}

function addPopups(map, name2popup, feature, layer) {
    var content = '';
    var label = '';
    if (REACTION == feature.properties.type) {
        var transport = feature.properties.transport ? "<p class='popup centre'>Is a transport reaction.</p>" : ""
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
        label = '<h2>' + feature.properties.name + "</h2>p class='popup centre'><i>id: </i>" + feature.properties.id + "</p>";
    }
    if (EDGE == feature.properties.type) {
        return
    }
    var e = feature.geometry.coordinates;
    var w = feature.properties.width / 2;
    var h = feature.properties.height / 2;
    var x = e[0], y = e[1];
    var southWest = map.unproject([x - w, y + h], 1),
        northEast = map.unproject([x + w, y - h], 1),
        bounds = new L.LatLngBounds(southWest, northEast);
    var size = $('#map').height();
    var popup = L.popup({autoPan: true, keepInView: true, maxWidth: size - 2, maxHeight: size - 2, autoPanPadding: [1, 1]}).setContent(content).setLatLng(bounds.getCenter());
    layer.bindPopup(popup).bindLabel(label); //.bindLabel('<i>' + feature.properties.name + '</i>', {noHide: true});
    if (feature.properties.name) {
        name2popup[feature.properties.name] = popup;
    }
    if (feature.properties.label) {
        name2popup[feature.properties.label] = popup;
    }
    if (feature.properties.id) {
        name2popup[feature.properties.id] = popup;
    }
    if (feature.properties.chebi) {
        name2popup[feature.properties.chebi] = popup;
    }
}


function getGeoJson(map, json, name2popup) {
    var edges = L.layerGroup([]);
    if (json == null || json.length == 0) {
        // pass
    } else if (json.length == 1) {
        getSimpleJson(map, json[0], name2popup, edges);
    } else {
        getComplexJson(map, json[0], json[1], name2popup, edges);
    }
    fitSimpleLabels();
    setAutocomplete(map, name2popup);
}


function getComplexJson(map, json_zo, json_zi, name2popup, edges) {
    var geojsonLayer = getSimpleJson(map, json_zo, name2popup, edges);
    var zo = map.getZoom();
    map.on('zoomend', function (e) {
        var zn = map.getZoom();
        if (zn >= 3 && zo < 3) {
            geojsonLayer = getJson(map, json_zi, name2popup, geojsonLayer, edges);
            fitSimpleLabels();
            setAutocomplete(map, name2popup);
        } else if (zn < 3 && zo >= 3) {
            geojsonLayer = getJson(map, json_zo, name2popup, geojsonLayer, edges);
            fitSimpleLabels();
            setAutocomplete(map, name2popup);
        } else {
            fitLabels(zn, zo);
            var layers = edges.getLayers();
            for (i in layers) {
                var e = layers[i];
                edges.removeLayer(e);
                e = L.polyline(e._latlngs, {
                    color: e.options['color'],
                    opacity: 1,
                    weight: e.options['weight'] * Math.pow(2, zn - zo),
                    lineCap: 'round',
                    lineJoin: 'round',
                    clickable: false,
                    fill: false
                })
                edges.addLayer(e);
                e.bringToBack();
            }
        }
        zo = map.getZoom();
    });
}

function fitSimpleLabels() {
    console.log('fitting labels into nodes');
    $('.count-icon', '#map').each(function (i, obj) {
        var width = $(this).width();
        var size = width < 8 ? 0 : Math.max(width / 5, 8);
        $(this).css({
            'font-size': size
        });
    });
}

function setAutocomplete(map, name2popup) {
    var availableTags = Object.keys(name2popup);
    $("#tags").autocomplete({
        source: availableTags
    });
    $('#tags').keypress(function (e) {
        if (e.keyCode == '13') {
            e.preventDefault();
            search(map, name2popup);
        }
    });
}

function fitLabels(zn, zo) {
    console.log('fitting labels into nodes');
    var pow = Math.pow(2, zn - zo);
    var width2css = {};
    $('.count-icon', '#map').each(function (i, obj) {
        var old_width = $(this).width();
        if (old_width in width2css) {
            $(this).css(width2css[old_width]);
        } else {
            var width = old_width * pow;
            var old_height = $(this).height();
            var height = old_height * pow;
            var size = width < 10 ? 0 : Math.max(width / 5, 8);
            var css = {
                'height': height,
                'width': width,
                'font-size': size
                //'top': $(this).offset().top + (old_height - height) / 2
            };
            $(this).css(css);
            width2css[old_width] = css;
        }
        var offset = $(this).offset();
        var shift = old_width * (1 - pow) / 2;
        $(this).offset({ top: offset.top + shift, left: offset.left + shift});//{ top: offset.top + (old_height - height) / 2, left: offset.left + (old_width - width) / 2});
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

function getSimpleJson(map, jsn, name2popup, edges) {
    return L.geoJson(jsn, {
        pointToLayer: function (feature, latlng) {
            return pnt2layer(map, feature, edges);
        },
        onEachFeature: function (feature, layer) {
            addPopups(map, name2popup, feature, layer);
        }
    }).addTo(map);
}

function getJson(map, jsn, name2popup, geojsonLayer, edges) {
    for (var prop in name2popup) {
        if (name2popup.hasOwnProperty(prop)) {
            delete name2popup[prop];
        }
    }
    edges.clearLayers();
    map.removeLayer(geojsonLayer);
    return getSimpleJson(map, jsn, name2popup, edges);
}

function search(map, name2popup) {
    var srch = document.search_form.search_input.value;
    if (srch && name2popup[srch]) {
        name2popup[srch].openOn(map);
    }
}

function gup(name) {
    name = new RegExp('[?&]' + name.replace(/([[\]])/, '\\$1') + '=([^&#]*)');
    return (window.location.href.match(name) || ['', ''])[1];
}

function centerMap() {
    map.setView([0, 0], map.getZoom());
}