import libsbgnpy.libsbgn as libsbgn
from libsbgnpy.libsbgnTypes import Language, GlyphClass, ArcClass, Orientation


SBO_2_GLYPH_TYPE = {'SBO:0000247': GlyphClass.SIMPLE_CHEMICAL, 'SBO:0000245': GlyphClass.MACROMOLECULE,
                    'SBO:0000421': GlyphClass.SIMPLE_CHEMICAL_MULTIMER, 'SBO:0000420': GlyphClass.MACROMOLECULE_MULTIMER,
                    'SBO:0000253': GlyphClass.COMPLEX, 'SBO:0000418': GlyphClass.COMPLEX_MULTIMER}
MARGIN = 16


def transform(((x, y), (w, h)), x_shift, y_shift, scale_factor):
    return shift(scale(convert_coordinates((x, y), (w, h)), scale_factor), x_shift, y_shift), scale((w, h), scale_factor)


def convert_coordinates((x, y), (w, h)):
    """
    Converts coordinates from the Tulip representation: (x, y) -- centre, (w, h) -- width and height
    to SBGN representation (x, y) -- top left corner, (w, h) -- width and height
    :return: SBGN-compatible coordinates: (x, y)
    """
    return shift((x, y), w / 2, h / 2)


def shift((x, y), x_shift=0, y_shift=0):
    return x - x_shift, y - y_shift


def scale((x, y), scale_factor=1):
    """
    Scales coordinates (x, y) by scale_factor.
    :return: scaled coordinates: (x, y)
    """
    return x * scale_factor, y * scale_factor


def get_transformation_factors(n2lo):
    x_min, y_min, x_max, y_max, h_min = None, None, None, None, None
    for v in n2lo.itervalues():
        if not isinstance(v, dict):
            v = {'': v}
        for ((x, y), (w, h)) in v.itervalues():
            if x_min is None or x - w / 2 < x_min:
                x_min = x - w / 2
            if x_max is None or x + w / 2 > x_max:
                x_max = x + w / 2
            if y_min is None or y - h / 2 < y_min:
                y_min = y - h / 2
            if y_max is None or y + h / 2 > y_max:
                y_max = y + h / 2
            if h_min is None or h < h_min:
                h_min = h
    scale_factor = 16.0 / h_min if h_min else 1
    w, h = x_max - x_min, y_max - y_min
    return scale_factor, (x_min, y_min), (w, h)


def save_as_sbgn(n2lo, e2lo, model, out_sbgn):
    # let's scale the map so that a minimal node has a width == 16 (so that the labels fit)
    scale_factor, (x_shift, y_shift), (w, h) = get_transformation_factors(n2lo)
    (w, h) = scale((w, h), scale_factor)
    (x_shift, y_shift) = shift(scale((x_shift, y_shift), scale_factor), MARGIN, MARGIN)

    # create empty sbgn
    sbgn = libsbgn.sbgn()

    # create map, set language and set in sbgn
    map = libsbgn.map()
    map.set_language(Language.PD)
    sbgn.set_map(map)

    # create a bounding box for the map
    box = libsbgn.bbox(0, 0, w + 2 * MARGIN, h + 2 * MARGIN)
    map.set_bbox(box)

    # glyphs with labels
    for comp in model.getListOfCompartments():
        c_id = comp.getId()
        c_name = comp.getName()
        if not c_name:
            c_name = c_id
        if c_id in n2lo:
            (x, y), (w, h) = transform(n2lo[c_id], x_shift, y_shift, scale_factor)
            g = libsbgn.glyph(class_=GlyphClass.COMPARTMENT, id=c_id)
            g.set_label(libsbgn.label(text=c_name, bbox=libsbgn.bbox(x, y, w, h)))
            g.set_bbox(libsbgn.bbox(x, y, w, h))
            map.add_glyph(g)

    for species in model.getListOfSpecies():
        s_id = species.getId()
        s_name = species.getName()
        glyph_type = GlyphClass.UNSPECIFIED_ENTITY
        sbo_term = species.getSBOTermID()
        if sbo_term:
            sbo_term = sbo_term.upper().strip()
            if sbo_term in SBO_2_GLYPH_TYPE:
                glyph_type = SBO_2_GLYPH_TYPE[sbo_term]
        if not s_name:
            s_name = s_id
        if s_id in n2lo:
            if isinstance(n2lo[s_id], dict):
                elements = n2lo[s_id].iteritems()
            else:
                elements = [(None, n2lo[s_id])]
            for r_id, coords in elements:
                (x, y), (w, h) = transform(coords, x_shift, y_shift, scale_factor)
                if not r_id or model.getReaction(r_id):
                    g = libsbgn.glyph(class_=glyph_type, id="%s_%s" % (s_id, r_id) if r_id else s_id,
                                      compartmentRef=species.getCompartment())
                    g.set_label(libsbgn.label(text=s_name, bbox=libsbgn.bbox(x + w * 0.1, y + h * 0.1, w * 0.8, h * 0.8)))
                    g.set_bbox(libsbgn.bbox(x, y, w, h))
                    map.add_glyph(g)

    # glyph with ports (process)
    for reaction in model.getListOfReactions():
        r_id = reaction.getId()
        if r_id in n2lo:
            (x, y), (w, h) = transform(n2lo[r_id], x_shift, y_shift, scale_factor)
            g = libsbgn.glyph(class_=GlyphClass.PROCESS, id=r_id)
            g.set_bbox(libsbgn.bbox(x, y, w, h))
            rev = reaction.getReversible()

            in_port = None
            for s_id in (species_ref.getSpecies() for species_ref in reaction.getListOfReactants()):
                edge_id = "-".join(sorted((s_id, r_id)))
                if edge_id in e2lo:
                    xy_list = e2lo[edge_id]
                    if not in_port:
                        port_x, port_y = shift(scale(xy_list[-2] if len(xy_list) > 2 else xy_list[-1], scale_factor),
                                               x_shift, y_shift)
                        in_port = libsbgn.port(x=port_x, y=port_y, id="%s__in" % r_id)
                        g.add_port(in_port)
                    sref_id = "%s_%s" % (s_id, r_id) if isinstance(n2lo[s_id], dict) else s_id
                    a = libsbgn.arc(class_=ArcClass.PRODUCTION if rev else ArcClass.CONSUMPTION,
                                    target=sref_id if rev else in_port.get_id(),
                                    source=in_port.get_id() if rev else sref_id, id="a_%s_%s" % (s_id, r_id))
                    s_x, s_y = shift(scale(xy_list[0], scale_factor), x_shift, y_shift)
                    a.set_start(libsbgn.startType(x=in_port.get_x() if rev else s_x, y=in_port.get_y() if rev else s_y))
                    a.set_end(libsbgn.endType(x=s_x if rev else in_port.get_x(), y=s_y if rev else in_port.get_y()))
                    map.add_arc(a)
            out_port = None
            for s_id in (species_ref.getSpecies() for species_ref in reaction.getListOfProducts()):
                edge_id = "-".join(sorted((s_id, r_id)))
                if edge_id in e2lo:
                    xy_list = e2lo[edge_id]
                    if not out_port:
                        port_x, port_y = shift(scale(xy_list[1] if len(xy_list) > 2 else xy_list[0], scale_factor),
                                               x_shift, y_shift)
                        out_port = libsbgn.port(x=port_x, y=port_y, id="%s__out" % r_id)
                        g.add_port(out_port)
                    a = libsbgn.arc(class_=ArcClass.PRODUCTION,
                                    target="%s_%s" % (s_id, r_id) if isinstance(n2lo[s_id], dict) else s_id,
                                    source=out_port.get_id(), id="a_%s_%s" % (r_id, s_id))
                    s_x, s_y = shift(scale(xy_list[-1], scale_factor), x_shift, y_shift)
                    a.set_end(libsbgn.startType(x=s_x, y=s_y))
                    a.set_start(libsbgn.endType(x=out_port.get_x(), y=out_port.get_y()))
                    map.add_arc(a)
            map.add_glyph(g)

            # if reaction.getNumReactants():
            #     in_port = libsbgn.port(x=x - w / 2, y=y + h / 2, id="%s_in" % r_id)
            #     g.add_port(in_port)
            # for s_id in (species_ref.getSpecies() for species_ref in reaction.getListOfReactants()):
            #     a = libsbgn.arc(class_=ArcClass.CONSUMPTION,
            #                     source="%s_%s" % (s_id, r_id) if isinstance(n2lo[s_id], dict) else s_id,
            #                     target=in_port.get_id(), id="a_%s_%s" % (s_id, r_id))
            #     (s_x, s_y), (s_w, s_h) = transform(n2lo[s_id][r_id] if isinstance(n2lo[s_id], dict) else n2lo[s_id],
            #                                        x_shift, y_shift, scale_factor)
            #     a.set_start(libsbgn.startType(x=s_x + 3 * s_w/2, y=s_y + s_h/2))
            #     a.set_end(libsbgn.endType(x=in_port.get_x(), y=in_port.get_y()))
            #     map.add_arc(a)
            # if reaction.getNumProducts():
            #     out_port = libsbgn.port(x=x + 3 * w / 2, y=y + h / 2, id="%s_out" % r_id)
            #     print x + 3 * w / 2, y + h / 2
            #     # g.add_port(out_port)
            # for s_id in (species_ref.getSpecies() for species_ref in reaction.getListOfProducts()):
            #     # a = libsbgn.arc(class_=ArcClass.PRODUCTION,
            #     #                 target="%s_%s" % (s_id, r_id) if isinstance(n2lo[s_id], dict) else s_id,
            #     #                 source=out_port.get_id(), id="a_%s_%s" % (r_id, s_id))
            #     (s_x, s_y), (s_w, s_h) = transform(n2lo[s_id][r_id] if isinstance(n2lo[s_id], dict) else n2lo[s_id],
            #                                        x_shift, y_shift, scale_factor)
            #     print "  ", model.getSpecies(s_id).getName(), s_x, s_y
            #     # a.set_end(libsbgn.startType(x=s_x - s_w/2, y=s_y + s_h/2))
            #     # a.set_start(libsbgn.endType(x=out_port.get_x(), y=out_port.get_y()))
            #     # map.add_arc(a)
            #
            # map.add_glyph(g)

    # write everything to a file
    sbgn.write_file(out_sbgn)