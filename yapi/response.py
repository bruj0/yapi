import logging
from pprint import pformat
from pprint import pprint
from yapi.utils import *
from yapi.extensions import Extensions
import requests
from requests_toolbelt.utils import dump
import json
from flatten_json import flatten
from box import Box
from box import BoxList
logger = None
class response:
    rsp = {}
    extensions = None
    body_variables = {}

    def __init__(self,rsp,variables,stage_name):
        self.variables = variables
        self.rsp=rsp
        self.extensions = Extensions(stage_name)
        global logger 
        logger = logging.LoggerAdapter(logging.getLogger(__name__), {'STAGE': stage_name})

    def validate(self,expected):
        rsp = self.rsp
        #logger.debug(f"Response data \n{pformat(rsp,width=1)}")
        logger.debug(f"Expected \n{pformat(expected,width=1)}")

        if rsp.status_code != int(expected['status_code']):
            logger.error(f"Received status code {rsp.status_code} != {expected['status_code']}\n {rsp.text}")
            exit(1)
        else:
            logger.info(f"<-Received status code OK {rsp.status_code} == {expected['status_code']}")

        response_text = rsp.text
        try:
            response_text = json.dumps(rsp.json(),indent=4, sort_keys=True)
        except json.decoder.JSONDecodeError:
            logger.info(f"<-Text received is not valid json")
            pass

        logger.info(f"<-Body of response:\n{response_text}")

        expected = format_keys(expected, self.variables)

        logger.debug(f"Formatted expected \n{pformat(expected,width=1)}")

        for key in expected:
            try:
                func = self.get_wrapped_create_function(expected[key].pop("$ext"),rsp.text)
            except (KeyError, TypeError, AttributeError):
                #logger.info(f"Testing func in {key}")
                pass
            else:
                func_data=func()
                logger.debug(f"Calling {func}: {pformat(func_data)}")            
        #Handling body variables                
            if key == 'body':
                rsp_json = Box(rsp.json(),ordered_box=True)
                logger.debug(f"Boxed response: {pformat(rsp_json)}")
                for body_vars in expected['body']:
                    body_var_str = f"rsp_json.{expected['body'][body_vars]}"
                    logger.debug(f"Body Variables adding: {expected['body'][body_vars]} accessing: {body_var_str}")
                    tmp = eval(body_var_str)
                    if isinstance(tmp,Box):
                            tmp=tmp.to_dict()
                    elif isinstance(tmp,BoxList):
                            tmp=tmp.to_list()

                    self.body_variables[body_vars] = tmp
                logger.debug(f"Body Variables:\n {pformat(self.body_variables)}")

    def get_body_variables(self):
        return self.body_variables

    def get_wrapped_create_function(self,ext,data):

        #logger.debug(f"ext={ext}")
        args = ext.get("extra_args") or ()
        kwargs = ext.get("extra_kwargs") or {}
        kwargs.update({ 'response_text': data})

        try:
            class_name, funcname = ext["function"].split(".")
        except ValueError as e:
            msg = f"Expected entrypoint in the form class.function: {e}"
            logger.exception(msg)
            exit(1)

        try:
            func = self.extensions.call_method(funcname)
        except AttributeError as e:
            msg = f"No function named {funcname} in {class_name} \n {e}"
            logger.exception(msg)

        #func = import_ext_function(ext["function"])
        logger.debug(f"Adding function {func} with args:{args} and kwargs:{kwargs.keys()}")
        @functools.wraps(func)
        def inner():
            return func(*args, **kwargs)

        inner.func = func

        return inner

