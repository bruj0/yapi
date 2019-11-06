#!/usr/bin/env python

from yapi.request import request as RestRequest
from yapi.response import response as RestResponse
from yapi.loader import yaml_loader as YamlLoader
from box import Box
import logging
from logging import getLogger

import sys, os, getopt
from pprint import pprint
from . import cfg
from . import __version__


logger = getLogger(__name__)

logger.info(f"Starting yapi {__version__}")

def main():
    yl = YamlLoader()
    #Will contain the "variables" block from the yaml
    variables = {
        'env_vars': dict(os.environ)
    }
    data = yl.load(cfg['in_file'])
    logger.info(f"Loading {cfg['in_file']}")


    #logger.debug(pprint(data))

    for stage in data['stages']:
        logger.info(f"Start of stage: {stage['name']}")
        request = RestRequest(stage['request'],variables)
        resp = request.run()
        RestResponse(resp,variables).validate(stage['response'])
        logger.info(f"End of stage: {stage['name']}")

    logger.info(f"Finished {cfg['in_file']}")
    exit(0)

if __name__== "__main__":
  main()