import os
import sys
import configparser
import configobj
import pandas as pd

"""
Consolidating useful functions
"""

def get_config(config_file):
    """
    Return dictionary values in a config 

    :param config_file: name of configuration file (including extension)
    """

    # define path to config file
    base = os.environ['PWD']
    config_repo = os.path.join(base, 'config')
    full_path = os.path.join(config_repo, config_file)

    # create config parser
    config = configobj.ConfigObj(full_path)
    
    return config




