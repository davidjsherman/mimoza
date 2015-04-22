import libsbgnpy.libsbgn as libsbgn
from libsbgnpy.libsbgnTypes import Language, GlyphClass, ArcClass, Orientation


SBO_2_GLYPH_TYPE = {'SBO:0000247': GlyphClass.SIMPLE_CHEMICAL, 'SBO:0000245': GlyphClass.MACROMOLECULE,
                    'SBO:0000421': GlyphClass.SIMPLE_CHEMICAL_MULTIMER, 'SBO:0000420': GlyphClass.MACROMOLECULE_MULTIMER,
                    'SBO:0000253': GlyphClass.COMPLEX, 'SBO:0000418': GlyphClass.COMPLEX_MULTIMER}


def convert_coordinates(((x, y), (w, h)), scale_factor=1):
    """
    Converts coordinates from the Tulip representation: (x, y) -- centre, (w, h) -- width and height
    to SBGN representation (x, y) -- top left corner, (w, h) -- width and height
    :return: SBGN-compatible coordinates: (x, y), (w, h)
    """
    x, y = x - w/2, y - h/2
    return (x * scale_factor, y * scale_factor), (w * scale_factor, h * scale_factor)


def save_as_sbgn((d_w, d_h), n2lo, e2lo, model, out_sbgn):
    # let's scale the map so that a minimal node has a width == 16 (so that the labels fit)
    scale_factor = 16 / min((v[1][0] for v in n2lo.itervalues() if not isinstance(v, dict)))

    # create empty sbgn
    sbgn = libsbgn.sbgn()

    # create map, set language and set in sbgn
    map = libsbgn.map()
    map.set_language(Language.PD)
    sbgn.set_map(map)

    # create a bounding box for the map
    box = libsbgn.bbox(x=0, y=0, w=d_w, h=d_h)
    map.set_bbox(box)

    # glyphs with labels
    for comp in model.getListOfCompartments():
        c_id = comp.getId()
        c_name = comp.getName()
        if not c_name:
            c_name = c_id
        if c_id in n2lo:
            (x, y), (w, h) = convert_coordinates(n2lo[c_id], scale_factor)
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
                (x, y), (w, h) = convert_coordinates(coords, scale_factor)
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
            (x, y), (w, h) = convert_coordinates(n2lo[r_id], scale_factor)
            g = libsbgn.glyph(class_=GlyphClass.PROCESS, id=r_id, orientation=Orientation.HORIZONTAL)
            g.set_bbox(libsbgn.bbox(x, y, w, h))
            for s_id in (species_ref.getSpecies() for species_ref in reaction.getListOfReactants()):
                g.add_port(libsbgn.port(x=x - w/2, y=y + h/2, id="r_%s_%s" % (s_id, r_id)))
                a = libsbgn.arc(class_=ArcClass.CONSUMPTION,
                                source="%s_%s" % (s_id, r_id) if isinstance(n2lo[s_id], dict) else s_id,
                                target="r_%s_%s" % (s_id, r_id), id="a_%s_%s" % (s_id, r_id))
                (s_x, s_y), (s_w, s_h) = convert_coordinates(n2lo[s_id][r_id] if isinstance(n2lo[s_id], dict)
                                                             else n2lo[s_id], scale_factor)
                a.set_start(libsbgn.startType(x=s_x + 3 * s_w/2, y=s_y + s_h/2))
                a.set_end(libsbgn.endType(x=x - w/2, y=y + h/2))
                map.add_arc(a)
            for s_id in (species_ref.getSpecies() for species_ref in reaction.getListOfProducts()):
                g.add_port(libsbgn.port(x=x + 3 * w/2, y=y + h/2, id="r_%s_%s" % (r_id, s_id)))
                a = libsbgn.arc(class_=ArcClass.PRODUCTION,
                                target="%s_%s" % (s_id, r_id) if isinstance(n2lo[s_id], dict) else s_id,
                                source="r_%s_%s" % (r_id, s_id), id="a_%s_%s" % (r_id, s_id))
                (s_x, s_y), (s_w, s_h) = convert_coordinates(n2lo[s_id][r_id] if isinstance(n2lo[s_id], dict)
                                                             else n2lo[s_id], scale_factor)
                a.set_end(libsbgn.startType(x=s_x - s_w/2, y=s_y + s_h/2))
                a.set_start(libsbgn.endType(x=x + 3 * w/2, y=y + h/2))
                map.add_arc(a)
            map.add_glyph(g)

    # write everything to a file
    sbgn.write_file(out_sbgn)