#!/usr/bin/env python

from yapi.request import request as RestRequest
from yapi.response import response as RestResponse
from yapi.loader import yaml_loader as YamlLoader
from box import Box
import logging
from logging import getLogger

import sys, os, getopt
from pprint import pformat
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
        logger.info(f"Stage: {stage['name']}")
        request = RestRequest(stage['request'],variables)

        resp = request.run(cfg['dry_run'])

        if cfg['dry_run'] is True:
            exit(0)

        response = RestResponse(resp,variables)
        response.validate(stage['response'])
        body_variables = response.get_body_variables()
        variables['resp']=body_variables

        logger.info(f"Saved response variables: \n{pformat(body_variables)}")
        logger.info(f"End of stage: {stage['name']}\n\n")


    logger.info(f"Finished {cfg['in_file']}")

if __name__== "__main__":
  main()