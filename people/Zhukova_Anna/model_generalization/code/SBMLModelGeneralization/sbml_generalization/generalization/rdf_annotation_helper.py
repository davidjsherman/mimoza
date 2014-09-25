from libsbml import CVTermList, RDFAnnotationParser, BIOLOGICAL_QUALIFIER, CVTerm, BQB_OCCURS_IN, BQB_IS, BQB_IS_VERSION_OF


__author__ = 'anna'


def get_is_qualifier():
    return BQB_IS


def get_is_vo_qualifier():
    return BQB_IS_VERSION_OF


def get_qualifier_values(annotation, qualifier_type):
    if not annotation:
        return
    cv_terms = CVTermList()
    RDFAnnotationParser.parseRDFAnnotation(annotation, cv_terms)
    for i in xrange(cv_terms.getSize()):
        term = cv_terms.get(i)
        if BIOLOGICAL_QUALIFIER == term.getQualifierType() and qualifier_type == term.getBiologicalQualifierType():
            yield term.getResourceURI(0).replace("%3A", ":")


def add_annotation(element, qualifier, annotation):
    if not element.isSetMetaId():
        element.setMetaId("m_{0}".format(element.getId()))
    term = CVTerm()
    term.setQualifierType(BIOLOGICAL_QUALIFIER)
    term.setBiologicalQualifierType(qualifier)
    term.addResource(annotation)
    element.addCVTerm(term, True)


def get_taxonomy(model):
    occurs_in = get_qualifier_values(model.getAnnotation(), BQB_OCCURS_IN)
    for it in occurs_in:
        start = it.find("taxonomy")
        if start != -1:
            return it[start + len("taxonomy:"):].strip()
    return None