rm -rf WS/mitochondrion
gdal2tiles.py -p raster -z 0-3 -w none mitochondrion.jpeg WS/mitochondrion
rm -rf WS/mitochondrion/3
gdal2tiles.py -p raster -z 3-4 -w none mitochondrion_f.jpeg WS/mitochondrion