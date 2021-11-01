import pandas as pd
import numpy as np
import requests
from requests.api import request
import helper_functions as hf
import utils
import json


"""
This script will return a dataframe containing all financial filing information
for a given company. Currently a work in progress (as of 10/28)
"""

def get_company_facts_json(search_val, user_agent):
    """
    In progress
    """

    # get the cik number
    cik_df = hf.parse_tickers(search_val, hf.get_cik_values, exact=True)

    # use cik number acquired above to query
    cik = cik_df['cik_str'].astype(str).str.pad(10, side = 'left', fillchar = '0')

    # build url to sec company facts api
    url = utils.get_config('edgar.ini')['COMPANY_FACTS_BASE'] + cik[0] + '.json'

    # create header for request to sec api (requires an email address)
    header = {'User-Agent': user_agent}

    r = requests.get(url, headers=header)

    # extract us gaap elements from data
    gaap = r.json()['facts']['us-gaap']




def company_facts_df(search_val, user_agent):
    """
    In progress
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

    # create dictionary containing values
    d = {
        'key': key_l,
        'accn': accn_l,
        'unit': unit_l,
        'val': val_l,
        'form': form_l,
        'filed': filed_l,
        'fy': fy_l
    }

    df = pd.DataFrame(d)

    return df

