rm -rf WS/peroxisome
gdal2tiles.py -p raster -z 0-3 -w none peroxisome.jpeg WS/peroxisome
rm -rf WS/peroxisome/3
gdal2tiles.py -p raster -z 3-4 -w none peroxisome_f.jpeg WS/peroxisome