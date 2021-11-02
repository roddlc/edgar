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

# continue here