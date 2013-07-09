export PYTHONPATH := ./:$(PYTHONPATH)

# If you want to use your model specify the path to it below
MODEL = ./MODEL1111190000.xml
CHEBI = ./data/chebi.obo
all: $(MODEL)
	./main/main.py --model $(MODEL) --verbose --chebi $(CHEBI)
