from libsbml import CVTermList, RDFAnnotationParser, BIOLOGICAL_QUALIFIER, CVTerm, BQB_OCCURS_IN

__author__ = 'anna'


def getQualifierValue(annotation, qualifierType):
    if not annotation:
        return None
    cvTerms = CVTermList()
    RDFAnnotationParser.parseRDFAnnotation(annotation, cvTerms)
    for i in range(cvTerms.getSize()):
        term = cvTerms.get(i)
        if BIOLOGICAL_QUALIFIER == term.getQualifierType() and qualifierType == term.getBiologicalQualifierType():
            return term.getResourceURI(0).replace("%3A", ":")
    return None


def getAllQualifierValues(annotation, qualifierType):
    result = set()
    if not annotation:
        return result
    cvTerms = CVTermList()
    RDFAnnotationParser.parseRDFAnnotation(annotation, cvTerms)
    for i in range(cvTerms.getSize()):
        term = cvTerms.get(i)
        if BIOLOGICAL_QUALIFIER == term.getQualifierType() and qualifierType == term.getBiologicalQualifierType():
            result.add(term.getResourceURI(0).replace("%3A", ":"))
    return result


def getPrefixedQualifierValues(annotation, qualifierType, prefix):
    if not annotation:
        return None
    cvTerms = CVTermList()
    RDFAnnotationParser.parseRDFAnnotation(annotation, cvTerms)
    result = set()
    for i in range(cvTerms.getSize()):
        term = cvTerms.get(i)
        if BIOLOGICAL_QUALIFIER == term.getQualifierType() and qualifierType == term.getBiologicalQualifierType():
            value = term.getResourceURI(0).replace("%3A", ":")
            if value.find(prefix) != -1:
                result.add(value)
    return result


def addAnnotation(element, qualifierType, annotationValue):
    if not element.isSetMetaId():
        element.setMetaId("m_{0}".format(element.getId()))
    term = CVTerm()
    term.setQualifierType(BIOLOGICAL_QUALIFIER)
    term.setBiologicalQualifierType(qualifierType)
    term.addResource(annotationValue)
    element.addCVTerm(term, True)


def isAnnotationEmpty(element):
    if not element or not element.isSetAnnotation():
        return True
    annotation = element.getAnnotation()
    if not annotation:
        return True
    cvTerms = CVTermList()
    RDFAnnotationParser.parseRDFAnnotation(annotation, cvTerms)
    for i in range(cvTerms.getSize()):
        term = cvTerms.get(i)
        if term.getResources():
            return False
    return True


def getTaxonomy(model):
    occursIn = getAllQualifierValues(model.getAnnotation(), BQB_OCCURS_IN)
    for it in occursIn:
        start = it.find("taxonomy")
        if start != -1:
            return it[start + len("taxonomy:"):].strip()
    return None