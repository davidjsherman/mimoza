rm -rf peroxisome
gdal2tiles.py -p raster -z 0-2 -w none peroxisome.jpg peroxisome
gdal2tiles.py -p raster -z 3-4 -w none peroxisome_f.jpg peroxisome