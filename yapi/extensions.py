import logging
import json
from flatten_json import flatten
from pprint import pformat

logger = None


class Extensions:
    def __init__(self,stage_name):
        global logger 
        logger = logging.LoggerAdapter(logging.getLogger(__name__), {'STAGE': stage_name})

    def call_method(self, method_name):
        return getattr(self, method_name)

    def decode_vault_token(self,*args,**kwargs):
        import binascii
        def byte_xor(ba1, ba2):
            return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])

        #logger.debug(f"response_text={kwargs['response_text']}")

        try:
            encoded=kwargs['encoded']
            otp=kwargs['otp']
            path=kwargs['path']
            logger.debug(f"encoded={encoded} otp={otp} path={path}")
        except Exception as e:
            logger.exception(e)
            return False
        try:
            b_encoded = binascii.a2b_base64(f"{encoded}==")
            b_otp = otp.encode()
        except Exception as e:
            logger.exception(e)
            return False
        
        decoded=byte_xor(b_encoded,b_otp)
        decoded_str=f'{{"root_token": "{decoded.decode()}"}}'
        logger.debug(f"Decoded: {decoded_str}\nrepr={repr(decoded)}")

        return self.save_response(path=path,response_text=decoded_str)


    #reads a json file and returns a dictionary
    def read_json(self,*args,**kwargs):
        try:
            kwargs['sub_vars'] = kwargs['sub_vars'] if 'sub_vars' in kwargs else False
            logger.info(f"Reading {kwargs['path']} , sub_vars: {kwargs['sub_vars']}")
            f = open(f"{kwargs['path']}", 'r')
            data = json.load(f)
            
            f.close()
            if 'keys' in data:
               data['_keys'] = data.pop('keys') 
            if 'sub_vars' in kwargs:
                #ret = { 'ext': data }
                logger.debug(f"Returned data: {pformat(data)}")
                return data
            else:
                return data
        except FileNotFoundError:
            logger.exception(f"File not found: {kwargs['path']}")
            exit(1)

    def save_response(self,*args,**kwargs):
        logger.debug(f"Called save_response with {args} and {kwargs}")
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

    
