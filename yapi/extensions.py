import logging
import json
from flatten_json import flatten
from pprint import pformat

logger = logging.getLogger(__name__)


class Extensions:
    def call_method(self, method_name):
        return getattr(self, method_name)

    #reads a json file and returns a dictionary
    def read_json(self,*args,**kwargs):
        try:
            logger.info(f"Reading {kwargs['path']} , sub_vars: {kwargs['sub_vars']}")
            f = open(f"{kwargs['path']}", 'r')
            data = json.load(f)
            
            f.close()
            if 'sub_vars' in kwargs:
                ret = { 'ext': flatten(data) }
                logger.debug(f"Flatten data: {pformat(ret)}")
                return ret
            else:
                return data
        except FileNotFoundError:
            logger.exception(f"File not found: {kwargs['path']}")
            exit(1)

    def save_response(self,*args,**kwargs):
        #logger.debug(f"Called save_response with {args} and {kwargs}")
        try:
            msg = f"Writing to {kwargs['path']}"
            if 'key' in kwargs:
                msg=f"{msg}, using key: {kwargs['key']}"
            logger.info(msg)
            f = open(f"{kwargs['path']}", 'w')
            if 'key' in kwargs:
                data = json.loads(kwargs['response_text'])
                if kwargs['key'] in data:
                    json.dump(data[kwargs['key']],f)
                else:
                    logger.error(f"Key {kwargs['key']} not found in return text")
                    return False
            else:
                f.write(kwargs['response_text'])
            f.close()
            return True
        except Exception as e:
            logger.exception(f"Couldnt write to : {kwargs['path']} {e}")     

    
