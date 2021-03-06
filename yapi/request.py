import logging
from pprint import pformat
from yapi.extensions import Extensions
import requests
from requests_toolbelt.utils import dump
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
from yapi.utils import *
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# for k,v in  logging.Logger.manager.loggerDict.items()  :
#         print('+ [%s] {%s} ' % (str.ljust( k, 20)  , str(v.__class__)[8:-2]) )
#         if not isinstance(v, logging.PlaceHolder):
#             for h in v.handlers:
#                 print('     +++',str(h.__class__)[8:-2] )
logger = None


class request():
    variables = {}
    extensions = None
    request_args = {}
    stage_name = None
    logger = None

    def __init__(self, rspec, variables, stage_name):
        self.variables = variables
        self.extensions = Extensions(stage_name)
        self.stage_name = stage_name
        global logger
        logger = logging.LoggerAdapter(
            logging.getLogger(__name__), {'STAGE': stage_name})

        logger.debug(f"Data passed to request:\n{pformat(rspec)}")

        expected = {
            "method",
            "url",
            "headers",
            "data",
            "params",
            "auth",
            "json",
            "verify",
            "files",
            "stream",
            "timeout",
            "cookies",
            "cert",
            # "hooks",
            "follow_redirects",
        }

        check_expected_keys(expected, rspec)

        self.request_args = self.get_request_args(rspec)

    def run(self, dry_run):
        with requests.Session() as session:
            ra = self.request_args

            json_body = ra['json'] if 'json' in ra else None

            req = requests.Request(
                ra['method'], ra['url'], json=json_body)
            if 'headers' in ra:
                req.headers = ra['headers']

            logger.info(f"->URL: {req.url}")
            logger.info(f"->Method: {req.method}")
            if 'json' in ra:
                logger.info(
                    f"->Body:\n{json.dumps(req.json,indent=4, sort_keys=True)}")

# Exit if its a dry run
            if dry_run is True:
                return False

            prepped = req.prepare()

            response = session.send(prepped, verify=False)
            data = dump.dump_response(response)
            logger.debug(f"Response={data.decode('utf-8')}")
            return response

    # TODO
    # add test_block_config
    def get_request_args(self, rspec):

        request_args = {}

        # Ones that are required and are enforced to be present by the schema
        required_in_file = ["method", "url"]

        optional_in_file = [
            "json",
            "data",
            "params",
            "headers",
            "files",
            "timeout",
            "cert",
            "auth"
        ]
        optional_with_default = {"verify": True, "stream": False}
        # METHOD
        if "method" not in rspec:
            logger.debug("Using default GET method")
            rspec["method"] = "GET"

        # CONTENT
        content_keys = ["data", "json", "files"]

        in_request = [c for c in content_keys if c in rspec]
        if len(in_request) > 1:
            # If more than one content defined raise an exception
            if set(in_request) != {"data", "files"}:
                raise f"Can only specify one type of request data in HTTP request (tried to send {','.join(in_request)})"

        # HEADERS
        headers = rspec.get("headers", {})
        has_content_header = "content-type" in [h.lower()
                                                for h in headers.keys()]

        if "files" in rspec:
            if has_content_header:
                logger.warning(
                    "Tried to specify a content-type header while sending a file - this will be ignored"
                )
                rspec["headers"] = {
                    i: j for i, j in headers.items() if i.lower() != "content-type"
                }

        # Substitute variables from env_vars and saved from the response in a previous stage
        fspec = format_keys(rspec, self.variables)

        request_args = add_request_args(
            request_args, fspec, required_in_file, False)
        request_args = add_request_args(
            request_args, fspec, optional_in_file, True)

        logger.debug(f"Data after env_vars substitution:\n{pformat(fspec)}")

        if "auth" in fspec:
            request_args["auth"] = tuple(fspec["auth"])

        if "cert" in fspec:
            if isinstance(fspec["cert"], list):
                request_args["cert"] = tuple(fspec["cert"])

        if "timeout" in fspec:
            # Needs to be a tuple, it being a list doesn't work
            if isinstance(fspec["timeout"], list):
                request_args["timeout"] = tuple(fspec["timeout"])

        # Traverse optional parts of the request
        # Will execute any $ext function
        for key in optional_in_file:
            try:
                func = self.get_wrapped_create_function(
                    request_args[key].pop("$ext"))
                #logger.debug(f"Calling $ext function at {func}")
            except (KeyError, TypeError, AttributeError):
                #logger.info(f"Testing func in {key}")
                pass
            else:
                logger.debug(f"Calling {func} from {key}")
                self.variables['ext'] = func()

            # Substitute in the part with ext variables
            if key in request_args:
                logger.debug(
                    f"Reformatting request_args[{key}]\n{pformat(request_args[key])}")
                request_args[key] = format_keys(
                    request_args[key], self.variables, False)
                logger.debug(
                    f"Result request_args[{key}]\n{pformat(request_args[key])}")

        # If there's any nested json in parameters, urlencode it
        # if you pass nested json to 'params' then requests silently fails and just
        # passes the 'top level' key, ignoring all the nested json. I don't think
        # there's a standard way to do this, but urlencoding it seems sensible
        # eg https://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter
        # > ...represented in an OAuth 2.0 request as UTF-8 encoded JSON (which ends
        # > up being form-urlencoded when passed as an OAuth parameter)
        for key, value in request_args.get("params", {}).items():
            if isinstance(value, dict):
                request_args["params"][key] = quote_plus(json.dumps(value))

        for key, val in optional_with_default.items():
            request_args[key] = fspec.get(key, val)

        # TODO
        # requests takes all of these - we need to parse the input to get them
        # "cookies",

        # These verbs _can_ send a body but the body _should_ be ignored according
        # to the specs - some info here:
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods
        if request_args["method"] in ["GET", "HEAD", "OPTIONS"]:
            if any(i in request_args for i in ["json", "data"]):
                logger.warn(
                    "You are trying to send a body with a HTTP verb that has no semantic use for it"
                )
        logger.debug(f"Final request_args\n{pformat(request_args)}")
        return request_args

    def get_wrapped_create_function(self, ext):

        # logger.debug(f"ext={ext}")
        args = ext.get("extra_args") or ()
        kwargs = ext.get("extra_kwargs") or {}

        try:
            class_name, funcname = ext["function"].split(".")
        except ValueError as e:
            msg = f"Expected entrypoint in the form class.function: {e}"
            logger.exception(msg)

        try:
            func = self.extensions.call_method(funcname)
        except AttributeError as e:
            msg = f"No function named {funcname} in {class_name} \n {e}"
            logger.exception(msg)

        #func = import_ext_function(ext["function"])
        logger.debug(
            f"Adding function {func} with args:{args} and kwargs:{kwargs}")

        @functools.wraps(func)
        def inner():
            return func(*args, **kwargs)

        inner.func = func

        return inner
