# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-11-20 15:54
from __future__ import unicode_literals

import logging
import os
import shutil
import tempfile
import zipfile

import boto3

from django.conf import settings
from django.contrib.gis.utils import LayerMapping
from django.db import migrations

logger = logging.getLogger(__name__)


CENSUS_BLOCK_LAYER_MAPPING = {
    'geom': 'POLYGON',
    'overall_score': 'OVERALL_SC'
}

NEIGHBORHOOD_WAYS_LAYER_MAPPING = {
    'geom': 'LINESTRING',
    'tf_seg_str': 'TF_SEG_STR',
    'ft_seg_str': 'FT_SEG_STR',
    'xwalk': 'XWALK',
    'ft_bike_in': 'FT_BIKE_IN',
    'tf_bike_in': 'TF_BIKE_IN',
    'functional': 'FUNCTIONAL'
}


def geom_from_results_url(shapefile_key):
    """ Downloads and extracts a zipped shapefile and returns the containing temporary directory.
    """
    logger.info('importing results back from shapefile: {sfile}'.format(sfile=shapefile_key))
    tmpdir = tempfile.mkdtemp()
    local_zipfile = os.path.join(tmpdir, 'shapefile.zip')
    s3_client = boto3.client('s3')
    s3_client.download_file(settings.AWS_STORAGE_BUCKET_NAME,
                            shapefile_key,
                            local_zipfile)
    with zipfile.ZipFile(local_zipfile, 'r') as zip_handle:
        zip_handle.extractall(tmpdir)
    return tmpdir


def s3_job_url(job, filename):
    return 'results/{uuid}/{filename}'.format(uuid=job.uuid, filename=filename)


def add_results_geoms(apps, schema_editor):
    AnalysisJob = apps.get_model('pfb_analysis', 'AnalysisJob')
    CensusBlocksResults = apps.get_model('pfb_analysis', 'CensusBlocksResults')
    NeighborhoodWaysResults = apps.get_model('pfb_analysis', 'NeighborhoodWaysResults')
    for job in AnalysisJob.objects.all():
        try:
            blocks_tmpdir = geom_from_results_url(s3_job_url(job, 'neighborhood_census_blocks.zip'))
            block_shpfiles = [filename for filename in
                              os.listdir(blocks_tmpdir) if filename.endswith('shp')]
            blocks_file = os.path.join(blocks_tmpdir, block_shpfiles[0])
            blocks_layer_map = LayerMapping(CensusBlocksResults,
                                            blocks_file,
                                            CENSUS_BLOCK_LAYER_MAPPING)
            blocks_layer_map.save()
            CensusBlocksResults.objects.filter(job=None).update(job=job)

            ways_tmpdir = geom_from_results_url(s3_job_url(job, 'neighborhood_ways.zip'))
            ways_shpfiles = [filename for filename in
                             os.listdir(ways_tmpdir) if filename.endswith('shp')]
            ways_file = os.path.join(ways_tmpdir, ways_shpfiles[0])
            ways_layer_map = LayerMapping(NeighborhoodWaysResults,
                                          ways_file,
                                          NEIGHBORHOOD_WAYS_LAYER_MAPPING)
            ways_layer_map.save()
            NeighborhoodWaysResults.objects.filter(job=None).update(job=job)
        except:
            logger.exception('ERROR: {}'.format(str(job.uuid)))
        finally:
            shutil.rmtree(blocks_tmpdir, ignore_errors=True)
            shutil.rmtree(ways_tmpdir, ignore_errors=True)


class Migration(migrations.Migration):

    dependencies = [
        ('pfb_analysis', '0031_censusblocksresults_neighborhoodwaysresults'),
    ]

    operations = [
        migrations.RunPython(add_results_geoms, reverse_code=migrations.RunPython.noop)
    ]
