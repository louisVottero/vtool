import os
import json
import logging.config
import util

def setup_logging( default_path='logging.json',
                   level = None,
                   env_key='LOG_CFG' ):
    """
    Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
            
        if level:
            config['root']['level'] = level
        logging.config.dictConfig(config)
    

def get_logger(name):
    log = logging.getLogger(name)
    if util.is_in_maya():
        log.setLevel(logging.CRITICAL)
    
    return log