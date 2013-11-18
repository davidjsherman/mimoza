rm -rf export
mkdir export
svn export SBMLModelGeneralization export/SBMLModelGeneralization
cp export/SBMLModelGeneralization/sbml_generalization/runner/main.py export/SBMLModelGeneralization/main.py
rm -rf export/SBMLModelGeneralization/sbml_generalization/runner
cp MODEL1111190000.xml export/SBMLModelGeneralization/MODEL1111190000.xml
cd export 
zip -r ../SBMLModelGeneralization.zip SBMLModelGeneralization
cd ..
rm -rf export

