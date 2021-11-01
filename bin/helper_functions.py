
import pandas as pd
import numpy as np
import requests
import os
import sys
import json
import utils


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
    Parse the tickers for specific company names (e.g., Apple, Microsoft).

    Args:
        search_val (str): Company name as listed on stock market exchange 
            (e.g., 'Apple Inc.', 'Microsoft Corporation').
        lookup_table (dataframe): Table to be searched for search_val.
        exact (bool): Specifies if company name should be exact or partial
            match to company's name on stock exchange (e.g., 'Apple Inc' v.
            'Apple'). If True, match will be done on exact name. If false, 
            will peform partial match.
    
    Returns:
        dataframe: records from lookup_table that match with search_val.

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


def get_submission_metadata(search_val,
                            user_agent,
                            exact = True):
    """
    Return a dataframe containing the metadata for SEC submissions by the 
    queried company.

    Args:
        search_val (str): Company name (e.g., 'Microsoft Corporation') to search
        user_agent (str): Name and email to be included with data request to SEC 
            API. This is required to submit the request. This field is formatted
            'FirstName LastName email@domain'.
        exact (bool, default True): Whether or not to match records along exact
            company name match. For example, if True, 'Microsoft' will not match
            to 'Microsoft Corporation'. On the flip side, if False, 'Apple' will match
            to 'Apple Inc' and other companies like 'Apple Hospitality REIT, Inc.'
    
    Returns:
        dataframe: The metadata for all submissions by the company to the SEC is 
            retured as a dataframe containing information such as:
                - accessionNumber
                - filingDate
                - reportDate
                - form (e.g., 10-K, 10-Q)
    """

    cik_df = parse_tickers(search_val, get_cik_values, exact)

    # extract ticker from cik (a dataframe)
    cik = cik_df['cik_str'].astype(str).str.pad(10, side = 'left', fillchar = '0')


    # build url
    url = utils.get_config('edgar.ini')['SUBMISSIONS_BASE'] + cik[0] + '.json'

    # create header for request to sec api (requires an email address)
    header = {'User-Agent': user_agent}

    result = requests.get(url, headers = header)

    # get recent filings from the json object
    df = pd.DataFrame(result.json()['filings']['recent'])

    return df





