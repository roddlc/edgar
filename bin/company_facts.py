import pandas as pd
import numpy as np
import requests
from requests.api import request
#import helper_functions as hf
import utils
import json
import os


"""
This script will return a dataframe containing all financial filing information
for a given company. Currently a work in progress (as of 10/28)
"""

def get_company_facts_json(search_val, user_agent, exact = True):
    """
    Submits request to SEC API and returns JSON containing multiple years of 
    company submissions to the SEC.

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
        dictionary: Raw JSON output returned from request sent to SEC API.
    """

    # get the cik number
    cik_df = utils.parse_tickers(search_val, utils.get_cik_values, exact = exact)

    # use cik number acquired above to query
    cik = cik_df['cik_str'].astype(str).str.pad(10, side = 'left', fillchar = '0')

    # build url to sec company facts api
    url = utils.get_config('edgar.ini')['COMPANY_FACTS_BASE'] + cik[0] + '.json'

    # create header for request to sec api (requires an email address)
    header = {'User-Agent': user_agent}

    r = requests.get(url, headers = header)

    # extract us gaap elements from data
    gaap = r.json()['facts']['us-gaap']

    return gaap




def company_facts_df(search_val, user_agent, 
                     export = False, outfile = None):
    """
    Pull all company facts as dataframe.

    Args:
        search_val (str): Company name (e.g., 'Microsoft Corporation') to search
        user_agent (str): Name and email to be included with data request to SEC 
            API. This is required to submit the request. This field is formatted
            'FirstName LastName email@domain'.
        exact (bool, default True): Whether or not to match records along exact
            company name match. For example, if True, 'Microsoft' will not match
            to 'Microsoft Corporation'. On the flip side, if False, 'Apple' will match
            to 'Apple Inc' and other companies like 'Apple Hospitality REIT, Inc.'
        export (default, False): Binary indicating whether the resulting dataframe
            should be export to CSV.
        outpath (default, None): Path to export assuming export param is set to True.

    Returns:
        dataframe: a dataframe containing all the company facts in recent years
            from the queried company
    """

    # get json with company fact data
    facts = get_company_facts_json(search_val, user_agent)


    # the following lists will be filled by for loop below
    key_l = []
    accn_l = []
    val_l = []
    unit_l = []
    form_l = []
    filed_l = []
    fy_l = []
    quarter_l = []
    end_l = []

    for key in facts.keys():
            
        # accn values
        #print(key)
        
        # get unique unit
        unit = list(facts[key]['units'].keys())[0]
        
        for n in range(len(facts[key]['units'][unit])):
            
            accn = facts[key]['units'][unit][n]['accn']
            accn_l.append(accn)
            
            unit_l.append(unit)
            
            key_l.append(key)
            
            val = facts[key]['units'][unit][n]['val']
            val_l.append(val)
            
            form = facts[key]['units'][unit][n]['form']
            form_l.append(form)
            
            filed = facts[key]['units'][unit][n]['filed']
            filed_l.append(filed)
            
            fy = facts[key]['units'][unit][n]['fy']
            fy_l.append(fy)

            end = facts[key]['units'][unit][n]['end']
            end_l.append(end)

            quarter = facts[key]['units'][unit][n]['fp']
            quarter_l.append(quarter)

    # create dictionary containing values
    d = {
        'key': key_l,
        'accn': accn_l,
        'unit': unit_l,
        'val': val_l,
        'form': form_l,
        'end': end_l,
        'filed': filed_l,
        'fy': fy_l
    }

    df = pd.DataFrame(d)

    if export:

        # get path to out dir
        full_path = str(os.getcwd()) + str(utils.get_config('edgar.ini')['OUTPATH']) + outfile
        
        df.to_csv(full_path)

    return df

