
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import requests
import os
import sys
import json

from requests.api import head
import utils


"""
This script contains various helper functions for processing data via
the SEC EDGAR API.
"""


def get_cik_and_ticker_values():
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

    # duplicate the title column, but with whitespace and punctuation removed
    # so that minor things like 'Apple Inc' v 'Apple Inc.' don't cause search
    # issues
    df['title_exact'] = df['title'].map(lambda x: ''.join(s for s in x if s.isalnum()))

    # set to lower case as well to avoid case-related issues
    df['title_exact'] = df['title_exact'].str.lower()

    # search for company name
    if exact:
        
        try:
            search_val = ''.join(s for s in search_val if s.isalnum())
            
            # check company name
            name_match = df[df['title_exact'] == search_val]

            # check ticker
            ticker_match = df[df['ticker'].str.lower() == search_val]

            # include a check for empty search result
            if len(name_match) == 0 and len(ticker_match) == 0:
                #print('Error')
                raise ValueError
                
        except ValueError: # consider adding a logger to create log files
            print('The search came up empty.')
    
    else:

        name_match = df[df['title'].str.contains(search_val, case = False)]

        ticker_match = df[df['ticker'].str.contains(search_val, case = False)]
    
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


    # build url
    url = utils.get_config('edgar.ini')['SUBMISSIONS_BASE'] + cik[0] + '.json'

    # create header for request to sec api (requires an email address)
    header = {'User-Agent': user_agent}

    result = requests.get(url, headers = header)

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

    archives_base = utils.get_config('edgar.ini')['ARCHIVES_DIR_BASE']

    cik_df = parse_tickers(search_val, exact)

    # extract ticker from cik (a dataframe)
    cik = cik_df['cik_str'].astype(str).str.pad(10, side = 'left', fillchar = '0')

    full_path = os.path.join(archives_base, cik[0], submission, 'FilingSummary.xml')
    print(full_path)
    header = {'User-Agent': user_agent}

    xml = requests.get(full_path, headers = header)
    xml = xml.content

    return xml


def get_financial_report_metadata(search_val,
                                  submission,
                                  user_agent,
                                  exact = True):
    """
    Parse raw xml containing submission metadata.

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
        dataframe: DataFrame containing parsed information from summary xml.
    """
    
    cik_df = parse_tickers(search_val, exact)

    # extract ticker from cik (a dataframe)
    cik = cik_df['cik_str'].astype(str).str.pad(10, side = 'left', fillchar = '0')
    cik = cik[0]
    
    # for loop below will append dictionaries containing metadata for various
    # financial reports for the filing in question (e.g., income statement,
    # balance sheet
    metadata = []

    # build base url that will be used for each report
    base = utils.get_config('edgar.ini')['ARCHIVES_DIR_BASE']

    xml = get_summary_xml(search_val, submission, user_agent, exact = True)

    soup = BeautifulSoup(xml, 'lxml')

    reports = soup.find('myreports')

    for report in reports.find_all('report')[:-1]:
        data = {}
        data['report_short_name'] = report.shortname.text
        data['report_long_name'] = report.longname.text
        data['report_url'] = os.path.join(base + cik + submission + report.htmlfilename.text)

        metadata.append(data)
    
    metadata_df = pd.DataFrame(metadata)

    return metadata_df

