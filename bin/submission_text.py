import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import os
import utils
import helper_functions as hf
import requests


"""
SEC also publishes raw text files for various filing types. The API does not seem
to allow for querying all the financial metrics from one filing; rather, it seems the 
API requires you to get all company facts across all filings in last 10+ years.
The aim of this script is to leverage BeautifulSoup to parse the .txt files made
available by SEC to create clean dataframes for export.
"""

# consider creating a class to process text data..

def get_financial_statement(search_val,
                            submission,
                            user_agent,
                            statement = None):

    """
    Return a dataframe with the data for the statement in question.

    Args:
        search_val (str): Company name (e.g., 'Microsoft Corporation') to search.
        submission (str): Unique ID for the submission.
        user_agent (str): Name and email to be included with data request to SEC 
            API. This is required to submit the request. This field is formatted
            'FirstName LastName email@domain'.
        statement (str, default None): Name of the financial statement to return.
            Accepts "Income Statement", "Balance Sheet", or "Cash Flow".
    
    Returns:
        dataframe: DataFrame containing financial statement data for a given submission.
    """

    xml = hf.get_financial_report_metadata(search_val = search_val,
                                           submission = submission,
                                           user_agent = user_agent)
    
    # depending on statement arg passed, select the report_url for that statement
    # e.g., if "Income Statement", select report_url for https://www.sec.gov/Archives/edgar/data/789019/000156459021051992/R2.htm

    if statement == "Income Statement":

        url = xml.query('report_short_name == "INCOME STATEMENTS"')['report_url'].tolist()[0]
        print(url)

        header = {'User-Agent': user_agent}
        r = requests.get(url, headers = header)

    #print(r.content)

    elif statement == "Balance Sheet": #! consider replacing == with list of acceptable values for a .contains + casing = False

        # <code here>
        print('this is a placeholder')

    elif statement == "Cash Flow":

        # <code here>
        print('this is a placeholder')
    
    else:

        print("Error: You did not provide an acceptable value. Try 'Income Statement', 'Balance Sheet', or 'Cash Flow'")

    # having received web content, pivot to beautiful soup

    soup = BeautifulSoup(r, 'html')

    # parse soup and create dataframe

    # more here..
