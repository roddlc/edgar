import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import os
import utils
import helper_functions as hf


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
            Accepts "Income Statement", "Balance Sheet", or "Cash Flow Statement".
    
    Returns:
        dataframe: DataFrame containing financial statement data for a given submission.
    """