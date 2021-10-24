
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
This script contains various helper functions for processing data via
the SEC EDGAR API.
"""


def get_cik_values():
    """
    Pull CIK, ticker, and company title combinations from the SEC API. This
    function leverages the link in the edgar.ini file.
    """
    url = utils.get_config('edgar.ini')['TICKERS']

    r = requests.get(url)

    nested_dict = r.json()

    # create df from nested dictionary of cik, ticker, company combos
    # to facilitate reading and querying
    df = pd.DataFrame(nested_dict.values())

    return df


def parse_tickers(search_val, lookup_table, exact = True):
    """
    Parse the tickers for specific company names (e.g., Apple, Microsoft)

    Args:
        company (str): Company name as listed on stock market exchange (e.g.,
            'Apple Inc.', 'Microsoft Corporation'
        exact (bool): Specifies if company name should be exact or partial
            match to company's name on stock exchange (e.g., 'Apple Inc' v.
            'Apple'). If True, match will be done on exact name. If false, 
            will peform partial match.
    
    Returns:

    """
    
    search_val = search_val.lower()

    # run the function created above and have it be assigned to df var to 
    # facilitate query
    df = lookup_table()

    # duplicate the title column, but with whitespace and punctuation removed
    # so that minor things like 'Apple Inc' v 'Apple Inc.' don't cause search
    # issues
    df['title_exact'] = df['title'].map(lambda x: ''.join(s for s in x if s.isalnum()))

    # set to lower case as well to avoid case-related issues
    df['title_exact'] = df['title_exact'].str.lower()

    # search for company name
    if exact:
        search_val = ''.join(s for s in search_val if s.isalnum())
        result = df[df['title_exact'] == search_val]
    
    else:
        result = df[df['title'].str.contains(search_val, case = False)]
    
    return result


test = parse_tickers('apple inc', get_cik_values)
print(test)
