
import pandas as pd
import numpy as np
import requests
import os
import sys
import json

from requests.api import get
import utils

# https://www.sec.gov/Archives/edgar/cik-lookup-data.txt

"""
This script contains
"""


def get_cik_values():
    """
    
    """
    url = utils.get_config('edgar.ini')['URL']

    r = requests.get(url)
    #r = pd.read_csv(url, sep = ':')

    return r

test = get_cik_values()
print(test.json()[:5])

