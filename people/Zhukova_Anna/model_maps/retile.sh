rm -rf peroxisome
gdal2tiles.py -p raster -z 0-4 -w none peroxisome.jpg peroxisome
rm -rf peroxisome/3
rm -rf peroxisome/4
gdal2tiles.py -p raster -z 3-4 -w none peroxisome_f.jpg peroxisome