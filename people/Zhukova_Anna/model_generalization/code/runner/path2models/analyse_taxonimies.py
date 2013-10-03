from genericpath import isfile, isdir
from os import listdir
from shutil import copyfile
from libsbml import SBMLReader
import sys
from runner.path2models.main import ROOT_DIR
from utils.rdf_annotation_helper import getTaxonomy

__author__ = 'anna'


def main(argv=None):
    extract_bacteria()
    #get_taxonomies_main()
    #get_taxonomy_sense()
    #update_tree()


def get_taxonomies_main():
    bm_in_path = ROOT_DIR + "bacteria_1/"
    in_path = ROOT_DIR + "sorted_bacteria/"
    taxonomy_file = "taxo.txt"
    for d in listdir(in_path):
        d = in_path + d + "/"
        if not isdir(d):
            continue
        out_file = d + taxonomy_file
        with open(out_file, 'w') as out_f:
            for m in listdir(d):
                in_sbml = bm_in_path + m
                if not isfile(in_sbml) or in_sbml.find(".xml") == -1:
                    continue
                reader = SBMLReader()
                document = reader.readSBML(in_sbml)
                model = document.getModel()
                taxonomy = getTaxonomy(model)
                if not taxonomy:
                    print "TAXONOMY not found for ", in_sbml
                out_f.write(taxonomy + "\n")


def extract_fungi():
    bm_in_path = ROOT_DIR + "biomodels/"
    gen_path = ROOT_DIR + "gen_biomodels/"
    dist = ROOT_DIR + "fungi/"
    tax_ids = set()
    with open('ROOT_DIR + "taxidlist.txt', 'r') as f:
        for l in f:
            tax_id = l.replace('\n', '').strip()
            if tax_id:
                tax_ids.add(tax_id)
    print len(tax_ids)
    for m in listdir(bm_in_path):
        in_sbml = bm_in_path + m
        if not isfile(in_sbml) or in_sbml.find(".xml") == -1:
            continue
        reader = SBMLReader()
        document = reader.readSBML(in_sbml)
        model = document.getModel()
        taxonomy = getTaxonomy(model)
        if taxonomy in tax_ids:
            copyfile(gen_path + m, dist + m)


def extract_bacteria():
    bm_in_path = ROOT_DIR + "biomodels/"
    gen_path = ROOT_DIR + "gen_biomodels/"
    dist = ROOT_DIR + "bacteria/"
    dist1 = ROOT_DIR + "bacteria1/"
    tax_ids = set()
    with open(ROOT_DIR + "taxidlist_bacteria.txt", 'r') as f:
        for l in f:
            tax_id = l.replace('\n', '').strip()
            if tax_id:
                tax_ids.add(tax_id)
    print len(tax_ids)
    for m in listdir(bm_in_path):
        in_sbml = bm_in_path + m
        if not isfile(in_sbml) or in_sbml.find(".xml") == -1:
            continue
        reader = SBMLReader()
        document = reader.readSBML(in_sbml)
        model = document.getModel()
        taxonomy = getTaxonomy(model)
        if taxonomy in tax_ids:
            copyfile(gen_path + m, dist + m)
            copyfile(in_sbml, dist1 + m)


def get_taxonomy_sense():
    in_path = ROOT_DIR + "sorted_gen_biomodels/"
    taxonomy_file = "commontree.txt"
    for d in listdir(in_path):
        t_file = in_path + d + "/" + taxonomy_file
        print d
        org2count = {}
        with open(t_file, 'r') as f:
            org, count, prev = None, 0, 1
            for line in f:
                cur = line.count("+ ")
                if cur == 0:
                    continue
                if cur == 1:
                    if org:
                        org2count[org] = count + 1
                    org, count, prev = line[2:].replace('\n', ''), 0, 1
                elif cur <= prev:
                    count += 1
                    prev = cur
                else:
                    prev = cur
            if org:
                org2count[org] = count + 1
            print org2count


def update_tree():
    rs_3 = ["Coccidioides posadasii C735 delta SOWgp", "Phaeosphaeria nodorum SN15", "Laccaria bicolor S238N-H82",
            "Coprinopsis cinerea okayama7#130", "Scheffersomyces stipitis CBS 6054", "Podospora anserina S mat+",
            "Magnaporthe oryzae 70-15", "Aspergillus fumigatus Af293", "Moniliophthora perniciosa FA553",
            "Coccidioides immitis RS", "Neosartorya fischeri NRRL 181", "Schizophyllum commune H4-8",
            "Kluyveromyces lactis NRRL Y-1140", "Botryotinia fuckeliana B05.10", "Tuber melanosporum Mel28",
            "Yarrowia lipolytica CLIB122", "Uncinocarpus reesii 1704", "Sclerotinia sclerotiorum 1980 UF-70",
            "Debaryomyces hansenii CBS767", "Aspergillus clavatus NRRL 1", "Candida glabrata CBS 138",
            "Neurospora crassa OR74A"]
    rs_2 = ["Candida albicans SC5314", "Lodderomyces elongisporus NRRL YB-4239", "Postia placenta Mad-698-R",
            "Ashbya gossypii ATCC 10895", "Vanderwaltozyma polyspora DSM 70294", "Candida dubliniensis CD36",
            "Meyerozyma guilliermondii ATCC 6260", "Saccharomyces cerevisiae S288c", "Komagataella pastoris GS115",
            "Candida tropicalis MYA-3404", "Lachancea thermotolerans CBS 6340", "Clavispora lusitaniae ATCC 42720",
            "Zygosaccharomyces rouxii CBS 732"]
    rs_1 = ["Cryptococcus neoformans var. neoformans JEC21", "Cryptococcus neoformans var. neoformans B-3501A",
            "Aspergillus niger CBS 513.88", "Aspergillus nidulans FGSC A4", "Schizosaccharomyces pombe 972h-",
            "Malassezia globosa CBS 7966", "Fusarium graminearum PH-1", "Encephalitozoon cuniculi GB-M1",
            "Penicillium chrysogenum Wisconsin 54-1255", "Ustilago maydis 521", "Aspergillus flavus NRRL3357",
            "Aspergillus oryzae RIB40"]
    #w = Workbook()
    #ws = w.add_sheet(u'Fungi')

    with open(ROOT_DIR + 'fungi_commontree.txt', 'r') as tree:
        with open(ROOT_DIR + 'fungi_commontree1.txt', 'w') as out_tree:
            #i = 0
            for l in tree:
                depth = l.count('+ ')
                name = l.replace('+ ', '').replace('\n', '').replace('#', '$\\sharp$').strip()
                #ws.write(i, j, t)
                #j += 1
                template = lambda result: "{0}~{1}&{2}\\\\ \n".format('~.' * depth, name, result)
                if name in rs_3:
                    profile = ' + & + & - & +'
                    #ws.write(i, j, "3/4")
                    #out_tree.write(l.replace('\n', '') + ' 3/4\n')
                elif name in rs_2:
                    profile = ' + & - & - & +'
                    #ws.write(i, j, "2/4")
                    #out_tree.write(l.replace('\n', '') + ' 2/4\n')
                elif name in rs_1:
                    profile = ' + & - & - & -'
                    #ws.write(i, j, "1/4")
                    #out_tree.write(l.replace('\n', '') + ' 1/4\n')
                else:
                    profile = '& & &'
                    #out_tree.write(l)
                #i += 1
                out_tree.write(template(profile))

                #w.save('fungi.xls')


if __name__ == "__main__":
    sys.exit(main())