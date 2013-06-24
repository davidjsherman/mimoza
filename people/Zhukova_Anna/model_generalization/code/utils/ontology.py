#!/usr/bin/env python
# encoding: utf-8

__author__ = 'anna'

import os


def removeMiriamPrefix(urn):
    urn = urn.strip()
    miriam_prefix = "urn:miriam:"
    identifiers_org_prefix = "http://identifiers.org/"
    if 0 == urn.find(miriam_prefix):
        urn = urn[len(miriam_prefix):]
        start = urn.find(":")
        if start != -1 and urn[start + 1:].find(":") != -1: urn = urn[start + 1:]
    elif 0 == urn.find(identifiers_org_prefix):
        urn = urn[len(identifiers_org_prefix):]
        start = urn.find("/")
        if start != -1:
            if urn[start + 1:].find(":") != -1:
                urn = urn[start + 1:]
            else:
                urn = urn.replace("/", ":")
    return urn.strip()


def addMiriamPrefix(urn):
    miriam_prefix = "http://identifiers.org/"
    chebi_prefix = "obo.chebi/"
    return "{0}{1}{2}".format(miriam_prefix, chebi_prefix, urn)


def findChebi(annotations):
    for annotation in annotations:
        if annotation and annotation.lower().find("chebi") != -1:
            return annotation
    return None


def inducedOntology(terms, onto, relationships={"is_a"}):
    ontology = Ontology()
    ids = set([it.getId() for it in terms])
    for term in terms:
        t_id = term.getId()
        new_term = Term(t_id, term.getName(), ids & term.getParentIds())
        new_term.altIds = term.getAllIds()
        new_term.synonyms = term.getSynonyms()
        ontology.addTerm(new_term)
    for term_id, rels in onto.rel_map.iteritems():
        if not term_id in ids:
            continue
        for (subj, rel, obj) in rels:
            if rel in relationships and subj in ids and obj in ids:
                ontology.addRelationship(subj, rel, obj)
    for term in ontology.getAllTerms():
        for par_id in term.getParentIds():
            ontology.getTerm(par_id).addChild(term)
        # fix roots
    old_roots = onto.getRoots()
    new_roots = ontology.getRoots()
    for root in filter(lambda it: not (it.getId() in old_roots), new_roots):
        ancestors = set()
        for term in ontology.getAllTerms():
            if onto.isA(root.getId(), term.getId()):
                ancestors.add(term)
        # let us filter out too general ancestors
        ancestor_set = set(ancestors)
        for it in ancestors:
            for that in ancestors:
                if it != that and onto.isA(that.getId(), it.getId()):
                    ancestor_set -= {it}
                    break
        for a_term in ancestor_set:
            a_term.children |= {root}
            root.parents |= {a_term.getId()}
            ontology.roots -= {root}
    return ontology


def subOntology(onto, ids, relationships={"is_a"}, step=None):
    terms = set()

    def addT(term_id, step=None):
        if step is not None and step <= 0:
            return
        term = onto.getTerm(term_id)
        if term and not (term in terms):
            terms.add(term)
            step = step - 1 if step else None
            if "is_a" in relationships:
                for parent_id in term.getParentIds():
                    addT(parent_id, step)
            for (subj, rel, obj) in onto.getTermRelationships(term_id, None, 0):
                if not (rel in relationships):
                    continue
                addT(subj, step)
                addT(obj, step)
        else:
            return

    for t_id in ids:
        addT(t_id, step)
    return inducedOntology(terms, onto, relationships)


def save(onto, path):
    with open(path, 'w') as f:
        for term in onto.getAllTerms():
            f.write("[Term]\n")
            id_ = term.getId()
            f.write("id: {0}\n".format(id_))
            for a_id in term.getAllIds():
                if a_id == id_:
                    continue
                f.write("alt_id: {0}\n".format(a_id))
            name = term.getName()
            f.write("name: {0}\n".format(name))
            for syn in term.getSynonyms():
                if syn == name:
                    continue
                f.write('synonym: "{0}" RELATED [ChEBI:]\n'.format(syn))
            for parent in term.getParentIds():
                f.write("is_a: {0}\n".format(parent))
            for (subj, rel, obj) in onto.getTermRelationships(id_, None, 1):
                f.write("relationship: {1} {0}\n".format(obj, rel))
            f.write("\n")
        for rel in onto.getRelationships():
            f.write("[Typedef]\n")
            f.write("id: {0}\n".format(rel))
            f.write("name: {0}\n".format(rel.replace("_", " ")))
            f.write("is_cyclic: false\n")
            f.write("is_transitive: false\n")


def parse(obo_file):
    if not obo_file or obo_file.find(".obo") == -1 or not os.path.exists(obo_file):
        return None
    ontology = Ontology()
    term = None
    child2parents = {}
    with open(obo_file, 'r') as obo:
        parents = set()
        for line in obo:
            line = line.replace("\n", '')
            if line.find("[Term]") != -1:
                if term:
                    ontology.addTerm(term)
                    if parents:
                        child2parents[term.getId()] = parents
                    parents = set()
                term = Term()
                continue
            if not term:
                continue
            semicolon = line.find(":")
            if semicolon == -1:
                continue
            prefix = line[0:semicolon].strip()
            value = line[semicolon + 1: len(line)].strip()
            comment = value.find("!")
            if comment != -1:
                value = value[0:comment].strip()
            if prefix == "id":
                term.setId(value.lower())
            elif prefix == "alt_id":
                term.addAltId(value.lower())
            elif prefix == "name":
                term.setName(value)
            elif prefix == "is_a":
                parent = ontology.getTerm(value.lower())
                if parent:
                    parent.children |= {term}
                else:
                    parents.add(value.lower())
                term.parents |= {value.lower()}
            elif prefix == "relationship":
                comment_start = value.find("!")
                if comment_start != -1:
                    value = value[0:comment_start]
                first, second = value.strip().split(" ")
                ontology.addRelationship(term.getId(), first, second.lower())
            elif prefix == "synonym":
                start = value.find('"')
                if start == -1:
                    continue
                end = value.find('"', start + 1)
                if end == -1:
                    continue
                value = value[start + 1:end]
                term.addSynonym(value)
            elif prefix == "xref":
                value = value.strip()
                if not value:
                    continue
                comment = value.find('"')
                if comment != - 1:
                    value = value[:comment]
                modifier = value.find("{")
                if modifier != -1:
                    value = value[:modifier]
                term.addAltId(value.strip().lower().replace(" ", "."))

    if term:
        ontology.addTerm(term)
    for child, parents in child2parents.iteritems():
        child = ontology.getTerm(child)
        for parent in parents:
            ontology.getTerm(parent).children |= {child}
    return ontology


class Term:
    def __init__(self, t_id=None, name=None, parents=None, children=None):
        self.id = t_id.lower() if t_id else None
        self.altIds = set()
        self.name = name
        self.parents = set(parents) if parents else set()
        self.children = set(children) if children else set()
        self.synonyms = set()

    def getId(self):
        return str(self.id)

    def addAltId(self, t_id):
        self.altIds.add(t_id.lower())

    def getAllIds(self):
        return self.altIds | {self.id}

    def setId(self, t_id):
        self.id = t_id.lower()

    def getName(self):
        return str(self.name) if self.name else None

    def setName(self, name):
        self.name = name

    def addSynonym(self, synonym):
        self.synonyms.add(synonym)

    def getSynonyms(self):
        return set(self.synonyms)

    def getParentIds(self):
        return set(self.parents)

    def addParent(self, parent_id):
        self.parents.add(parent_id)

    def addChild(self, term):
        self.children.add(term)

    def getChildren(self, direct=True):
        result = set(self.children)
        if direct:
            return result
        for child in self.children:
            result |= child.getChildren(direct)
        return result

    def __str__(self):
        return "{0}({1})".format(self.getId(), self.getName())


def addToMap(mp, key, value):
    if key in mp:
        mp[key].add(value)
    else:
        mp[key] = {value}


def removeFromMap(mp, key, value):
    if key in mp:
        mp[key] -= {value}
        if not mp[key]:
            del mp[key]


class Ontology:
    def __init__(self):
        self.roots = set()
        self.id2term = {}
        self.alt_id2term = {}
        self.name2term_ids = {}
        self.rel_map = {}

    def getAllTerms(self):
        return set(self.id2term.values())

    def getLeaves(self):
        return set(filter(lambda it: not it.getChildren(), self.id2term.values()))

    def addRelationship(self, subj, rel, obj):
        relationship = (subj, rel, obj)
        addToMap(self.rel_map, subj, relationship)
        addToMap(self.rel_map, obj, relationship)
        addToMap(self.rel_map, rel, relationship)

    # role: 0 for any, 1 for subj, 2 for obj
    def getTermRelationships(self, term_id, rel=None, role=0):
        if not (term_id in self.rel_map):
            return set()
        relationships = set(self.rel_map[term_id])
        if rel:
            relationships = filter(lambda (subj, r, obj): rel == r, relationships)
        if 1 == role:
            relationships = filter(lambda (subj, r, obj): term_id == subj, relationships)
        if 2 == role:
            relationships = filter(lambda (subj, r, obj): term_id == obj, relationships)
        return relationships

    def getRelationships(self):
        result = set()
        for rel_set in self.rel_map.values():
            result |= {rel for (subj, rel, obj) in rel_set}
        return result

    def addTerm(self, term):
        if not term:
            return
        t_id = term.getId()
        self.id2term[t_id] = term
        for alt_id in term.getAllIds():
            alt_id = alt_id.lower()
            self.alt_id2term[alt_id] = term
        names = set(term.getSynonyms())
        names.add(term.getName())
        for name in names:
            name = name.lower()
            if not (name in self.name2term_ids):
                self.name2term_ids[name] = set()
            self.name2term_ids[name].add(t_id)
        if not term.getParentIds():
            self.roots.add(term)
        for child in term.getChildren():
            child.parents.add(t_id)
            self.roots -= {child}

    def removeTerm(self, term, brutally=False):
        if not term:
            return
        t_id = term.getId()
        if t_id in self.id2term:
            del self.id2term[t_id]
        for alt_id in term.getAllIds():
            alt_id = alt_id.lower()
            if alt_id in self.alt_id2term:
                del self.alt_id2term[alt_id]
        names = set(term.getSynonyms())
        names.add(term.getName())
        for name in names:
            name = name.lower()
            if name in self.name2term_ids:
                self.name2term_ids[name] -= {t_id}
                if not self.name2term_ids[name]:
                    del self.name2term_ids[name]
        parents = term.getParentIds()
        if not parents:
            self.roots -= {term}
        children = term.getChildren()
        for par_id in parents:
            par = self.getTerm(par_id)
            par.children -= {term}
            if not brutally:
                par.children |= children
        for child in children:
            child.parents -= term.getAllIds()
            if not brutally:
                child.parents |= parents
            if not child.parents:
                self.roots.add(child)
        relationships = self.getTermRelationships(t_id)
        if relationships:
            del self.rel_map[t_id]
            for (subj, rel, obj) in relationships:
                if t_id == subj and t_id != obj:
                    removeFromMap(self.rel_map, obj, (subj, rel, obj))
                elif t_id == obj:
                    removeFromMap(self.rel_map, subj, (subj, rel, obj))

    def getTerm(self, term_id):
        if not term_id:
            return None
        term_id = term_id.lower()
        if term_id in self.id2term:
            return self.id2term[term_id]
        if term_id in self.alt_id2term:
            return self.alt_id2term[term_id]
        return None

    def isA(self, child_id, parent_id):
        child = self.getTerm(child_id)
        parent = self.getTerm(parent_id)
        return parent in self.getParents(child, False, None, set())

    def partOf(self, part_id, whole_Ids):
        term = self.getTerm(part_id)
        if not term:
            return None
        partOf_ = lambda term: {obj for (subj, r, obj) in self.getTermRelationships(term.getId(), "part_of", role=1)}
        whole_Ids = {t_id.lower().strip() for t_id in whole_Ids}
        result = whole_Ids & partOf_(term)
        if result:
            return result
        term_set = {term}
        result = set()
        while term_set:
            items = set()
            for term in term_set:
                parents = term.getParentIds()
                wholes = partOf_(term)
                candidates = parents | wholes
                for it in candidates:
                    if (it in whole_Ids) and not self.isA(part_id, it):
                        result.add(it)
                        continue
                    candidate = self.getTerm(it)
                    result |= whole_Ids & partOf_(candidate)
                    result |= set(filter(lambda r: not self.isA(part_id, r), set(whole_Ids) & candidate.getParentIds()))
                    items.add(candidate)
            term_set = items
        return result

    def getParents(self, term, direct=True, rel=None, checked=None):
        if not checked:
            checked = set()
        parents = term.getParentIds() if not rel else {obj for (subj, rel, obj) in
                                                       self.getTermRelationships(term.getId(), rel, 1)}
        direct_parents = set(map(lambda t_id: self.getTerm(t_id), parents))
        if direct:
            return direct_parents
        result = set(direct_parents)
        checked.add(term)
        for parent in direct_parents:
            if not (parent in checked):
                result |= self.getParents(parent, direct, rel, checked)
        return result

    def getLevel(self, term):
        parents = self.getParents(term)
        if not parents:
            return [0]
        level = set()
        for p in parents:
            level |= set(self.getLevel(p))
        return [1 + i for i in level]

    def getEqualTerms(self, term, rel=None, direction=0):
        term_id = term.getId()
        equals = set()
        for (subj, rel, obj) in self.getTermRelationships(term_id, rel, direction):
            equals |= {subj, obj} - {term_id}
        return {self.getTerm(t_id) for t_id in equals}

    def getAnyChildren(self, term, direct=True, checked=set()):
        terms = {term} | self.getEqualTerms(term)
        direct_kids = set()
        for it in terms:
            children = it.getChildren(True)
            direct_kids |= children
            for ch in children:
                direct_kids |= self.getEqualTerms(ch)
        if direct:
            return direct_kids
        checked |= terms
        result = set(direct_kids)
        for kid in direct_kids - checked:
            result |= self.getAnyChildren(kid, direct, checked)
        return result

    def getAnyParents(self, term, direct=True, checked=set()):
        terms = {term} | self.getEqualTerms(term)
        direct_parents = set()
        for it in terms:
            parents = {self.getTerm(t_id) for t_id in it.getParentIds()}
            direct_parents |= parents
            for par in parents:
                direct_parents |= self.getEqualTerms(par)
        if direct:
            return direct_parents
        checked |= terms
        result = set(direct_parents)
        for parent in direct_parents - checked:
            result |= self.getAnyParents(parent, direct, checked)
        return result

    def getRoots(self):
        return set(self.roots)

    def getIdsByName(self, name):
        name = name.lower()
        return set(self.name2term_ids[name]) if name in self.name2term_ids else set()

    def commonPts(self, terms):
        if not terms:
            return None
        terms = set(terms)
        first = terms.pop()
        common = self.getAnyParents(first, False, set()) | self.getEqualTerms(first) | {first}
        # print " draft ", [t.getName() for t in common]
        for t in terms:
            # print "  and ", [t.getName() for t in self.getAnyParents(t, False) | self.getEqualTerms(t) | {t}]
            common &= self.getAnyParents(t, False, set()) | self.getEqualTerms(t) | {t}
            # print "  draft ", [t.getName() for t in common]
        result = set(common)
        # print " common ", [t.getName() for t in common]
        return filter(lambda it: not self.getAnyChildren(it, False) & result, common)

    def removeRelationships(self, relationships, brutally=False):
        for (subj_id, r, o_id) in relationships:
            if "is_a" == r:
                subj, obj = self.getTerm(subj_id), self.getTerm(o_id)
                if not subj or not obj:
                    continue
                subj.parents -= obj.getAllIds()
                obj.children -= {subj}
                if not brutally:
                    subj.parents |= obj.parents
                    for par in obj.parents:
                        self.getTerm(par).children.add(subj)
                if not subj.parents:
                    self.roots.add(subj)
            else:
                removeFromMap(self.rel_map, subj_id, (subj_id, r, o_id))
                removeFromMap(self.rel_map, o_id, (subj_id, r, o_id))
