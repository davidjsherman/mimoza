rm -rf htdocs/peroxisome
gdal2tiles.py -p raster -z 0-3 -w none peroxisome.jpg htdocs/peroxisome
rm -rf htdocs/peroxisome/3
gdal2tiles.py -p raster -z 3-4 -w none peroxisome_f.jpg htdocs/peroxisome