# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

import os
import json
import logging.config
from . import util


def setup_logging(default_path='',
                  level=None,
                  env_key='LOG_CFG'):
    """
    Setup logging configuration

    """
    if not default_path:
        current_dir = util.get_dirname()

        default_path = os.path.join(current_dir, 'logging.json')

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
