#!/bin/bash
# Run bna

dest='/home/luis/tmpjunk/'
city_shp_name='brooklynshp.shp'
shp_file="${dest}${city_shp_name}"
pfb_osm_file='brooklyn-newyork.osm'
osm_file="${dest}${pfb_osm_file}"
pfb_country='USA'
pfb_state='ny'
state_fips='36'
run_import_jobs=1
output_dir=$dest


# osmium extract -p /home/luis/tmpjunk/brooklyn.geojson \
# /home/luis/tmpjunk/new-york-latest.osm.pbf \
# -o /home/luis/tmpjunk/brooklyn-newyork.osm 

docker run --name pgrouting -it -e PFB_SHPFILE=$shp_file \
            -e PFB_OSM_FILE=$osm_file \
            -e PFB_COUNTRY=$pfb_country \
            -e PFB_STATE=$pfb_state \
            -e PFB_STATE_FIPS=$state_fips \
            -e NB_OUTPUT_DIR=$dest \
            -e RUN_IMPORT_JOBS=$run_import_jobs \
            -e PFB_DEBUG=1 \
            -v $output_dir:$dest \
            azavea/pfb-network-connectivity:0.19.0-pgrouting
