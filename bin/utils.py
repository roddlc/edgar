import os
import sys
#import configparser
import configobj
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import requests
import json

from requests.api import head
#import utils


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


"""
This script contains various helper functions for processing data via
the SEC EDGAR API.
"""


def get_cik_and_ticker_values():
    """
    Pull CIK, ticker, and company title combinations from the SEC API. This
    function leverages the link in the edgar.ini file.
    """

    url = get_config('edgar.ini')['TICKERS']
    
    try:
        r = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        print(
            f"A {type(e).__name__} error occurred.\n"
            f"Arguments: {e.args}\n"
            "\nConfirm that your Internet connection is stable."
        )

    nested_dict = r.json()

    # create df from nested dictionary of cik, ticker, company combos
    # to facilitate reading and querying
    df = pd.DataFrame(nested_dict.values())

    return df


def parse_tickers(search_val, exact = True):
    """
    Parse the tickers for specific company names (e.g., Apple, Microsoft).

    Args:
        search_val (str): Company name or ticker as listed on stock market exchange 
            (e.g., 'Apple Inc.'or 'AAPL'; 'Microsoft Corporation' or 'MSFT').
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
    df = get_cik_and_ticker_values()

    # strip title down to just alphanumeric characters
    df['title_alnum'] = df['title'].apply(lambda x: ''.join(s for s in x if s.isalnum()))\
        .str.lower()

    # search for company name
    if exact:
        
        try:
            # strip search val to just alnum characters
            search_val = ''.join(s for s in search_val if s.isalnum())
            
            # check company name
            name_match = df[df['title_alnum'] == search_val].reset_index()

            # check ticker
            ticker_match = df[df['ticker'].str.lower() == search_val].reset_index()

            # include a check for empty search result
            if len(name_match) == 0 and len(ticker_match) == 0:
                raise ValueError
                
        except ValueError: # consider adding a logger to create log files
            print('The search came up empty.')
            print('Consider trying "exact=False" and seeing if that',
                    'yields what you are looking for.')
            exit(1)
    
    else:

        name_match = df[df['title'].str.contains(search_val, case = False)].reset_index()

        ticker_match = df[df['ticker'].str.contains(search_val, case = False)].reset_index()
    
    # select result
    if len(name_match) == 0 and len(ticker_match) > 0:
        result = ticker_match

    elif len(name_match) > 0 and len(ticker_match) == 0:
        result = name_match
    
    elif len(name_match) > 0 and len(ticker_match) > 0:
        raise Exception('Returned both a name and ticker match')
    
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

    cik_df = parse_tickers(search_val, exact)

    # extract ticker from cik (a dataframe)
    cik = cik_df['cik_str'].astype(str).str.pad(10, side = 'left', fillchar = '0')

    #! need to handle situations where parse_tickers() returns more than one row

    # build url
    url = get_config('edgar.ini')['SUBMISSIONS_BASE'] + cik + '.json'

    # create header for request to sec api (requires an email address)
    header = {'User-Agent': user_agent}

    try:
        result = requests.get(url[0], headers = header)
    except requests.exceptions.ConnectionError as e:
        print(
            f"A {type(e).__name__} error occurred.\n"
            f"Arguments: {e.args}\n"
            "\nConfirm that your Internet connection is stable."
        )

    # get recent filings from the json object
    df = pd.DataFrame(result.json()['filings']['recent'])

    return df


def get_summary_xml(search_val, 
                    #lookup_table, 
                    submission, # consider connecting w/ metadata function
                    user_agent, 
                    exact = True):
    """
    Return xml content containing summary information for any given filing.

    Args:
        search_val (str): Company name (e.g., 'Microsoft Corporation') to search.
        submission (str): Unique ID for the submission.
        user_agent (str): Name and email to be included with data request to SEC 
            API. This is required to submit the request. This field is formatted
            'FirstName LastName email@domain'.
        exact (bool, default True): Whether or not to match records along exact
            company name match. For example, if True, 'Microsoft' will not match
            to 'Microsoft Corporation'. On the flip side, if False, 'Apple' will match
            to 'Apple Inc' and other companies like 'Apple Hospitality REIT, Inc.'
    
    Returns:
        xml content: Contains metadata specific to a particular filing.
    """

    archives_base = get_config('edgar.ini')['ARCHIVES_DIR_BASE']

    cik_df = parse_tickers(search_val, exact)

    # extract ticker from cik (a dataframe)
    cik = cik_df['cik_str'].astype(str).str.pad(10, side = 'left', fillchar = '0')

    full_path = os.path.join(archives_base, cik.values[0], submission, 'FilingSummary.xml')

    header = {'User-Agent': user_agent}

    try:
        xml = requests.get(full_path, headers = header)
    except requests.exceptions.ConnectionError as e:
        print(
            f"A {type(e).__name__} error occurred.\n"
            f"Arguments: {e.args}\n"
            "\nConfirm that your Internet connection is stable."
        )
    xml = xml.content

    return xml


#! consider moving this function to submission_text.py
def get_financial_report_metadata(search_val,
                                  submission,
                                  user_agent,
                                  csv_path = None,
                                  exact = True):
    """
    Parse raw xml containing submission metadata.

    Args:
        search_val (str): Company name (e.g., 'Microsoft Corporation') to search.
        submission (str): Unique ID for the submission.
        user_agent (str): Name and email to be included with data request to SEC 
            API. This is required to submit the request. This field is formatted
            'FirstName LastName email@domain'.
        csv_path (str, default None): path to output text file of metadata. If None,
            a dataframe will be returned in the console.
        exact (bool, default True): Whether or not to match records along exact
            company name match. For example, if True, 'Microsoft' will not match
            to 'Microsoft Corporation'. On the flip side, if False, 'Apple' will match
            to 'Apple Inc' and other companies like 'Apple Hospitality REIT, Inc.'
    
    Returns:
        dataframe: DataFrame containing parsed information from summary xml.
    """
    
    cik_df = parse_tickers(search_val, exact)

    # extract ticker from cik (a dataframe)
    cik = cik_df['cik_str'].astype(str).str.pad(10, side = 'left', fillchar = '0')
    cik = cik.values[0]
    
    # for loop below will append dictionaries containing metadata for various
    # financial reports for the filing in question (e.g., income statement,
    # balance sheet
    metadata = []

    # build base url that will be used for each report
    base = get_config('edgar.ini')['ARCHIVES_DIR_BASE']

    xml = get_summary_xml(search_val, submission, user_agent, exact = exact)
    soup = BeautifulSoup(xml, "html")

    reports = soup.find('myreports')

    for report in reports.find_all('report')[:-1]:
        data = {}
        data['report_short_name'] = report.shortname.text
        data['report_long_name'] = report.longname.text
        data['report_url'] = os.path.join(base, cik, submission, report.htmlfilename.text)

        metadata.append(data)
    
    metadata_df = pd.DataFrame(metadata)

    if csv_path:

        metadata_df.to_csv(csv_path, index = False)
        print('out')
    
    return metadata_df

#get_financial_report_metadata('MSFT', '000156459021002316', user_agent = 'test@test', csv_path='out/msft_10q_jan_2021.txt')
