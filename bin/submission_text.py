from multiprocessing.sharedctypes import Value
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import os
import utils
#import helper_functions as hf
import requests


"""
SEC also publishes raw text files for various filing types. The API does not seem
to allow for querying all the financial metrics from one filing; rather, it seems the 
API requires you to get all company facts across all filings in last 10+ years.
The aim of this script is to leverage BeautifulSoup to parse the .txt files made
available by SEC to create clean dataframes for export.
"""

class Edgar:
    """
    Company can be a ticker (e.g., MSFT for Microsoft) or a full name.
    """
    def __init__(
        self,
        company=None,
        #ticker=None,
        user_agent=None,
        statement=None,
        exact=True
    ):
        
        self.company = company
        #self.ticker = ticker
        self.user_agent = user_agent
        self.statement = statement
        self.exact = exact

    def submission_history(self):

        meta = utils.get_submission_metadata(self.company, self.user_agent, self.exact)
        return(meta)

    # consider creating a class to process text data..
    def __parse_soup(self, soup):
        
        # data to be populated by for loop below
        data = {}
        data['values'] = []
        data['section_divs'] = []
        data['col_headers'] = []
        
        for i, row in enumerate(soup.table.find_all('tr')):

            # get regular data (no header)
            if len(row.find_all('th')) == 0 and len(row.find_all('strong')) == 0:

                val = [i] + [r.text.strip() for r in row.find_all('td')]
                #print(val)
                data['values'].append(val)

            # get section divider
            elif len(row.find_all('th')) == 0 and len(row.find_all('strong')) != 0:

                section_div = [i] + [r.text.strip() for r in row.find_all('td')]
                #print(section_div)
                data['section_divs'].append(section_div)

            elif len(row.find_all('th')) != 0:

                header = [r.text.strip() for r in row.find_all('th')]
                #print(header)
                data['col_headers'].append(header)
        
        return data

    def __make_df(self, data_dict):
        # create header columns
        headers_str = list(map(str, data_dict['col_headers'][0]))

        # remove elements like '3 months listed'
        headers_str = [x for x in headers_str if 'Months' not in x and not x.isdigit()]
        
        # clean up the first column header.. this code could be made more elegant
        headers_str = [headers_str[0].replace("($)", "").replace(",", " and").replace("  ", " (") + ')']
        
        # populate dataframe with data and section dividers
        df = pd.DataFrame(data_dict['values'] + data_dict['section_divs'])
        
        # sort on index created by enumerate in parse_soup() above
        df.sort_values(by = 0, inplace = True)

        # now that data is sorted, we can drop 0
        df.drop([0], axis = 1, inplace = True)
        
        # create the column headers for the data
        new_col_headers = list(map(str, data_dict['col_headers'][1]))
        new_col_headers = [x for x in new_col_headers if not x.isdigit()]

        df.columns = headers_str + new_col_headers

        return df


    def get_financial_statement(self, 
                                submission,
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
        print('exact:', self.exact)
        xml = utils.get_financial_report_metadata(search_val = self.company,
                                                  user_agent = self.user_agent,
                                                  exact = self.exact,
                                                  submission = submission)
        
        # depending on statement arg passed, select the report_url for that statement
        # e.g., if "Income Statement", select report_url for https://www.sec.gov/Archives/edgar/data/789019/000156459021051992/R2.htm

        try:

            if statement == "Income Statement":

                url = xml.query('report_short_name == "INCOME STATEMENTS"')['report_url'].tolist()[0]

                header = {'User-Agent': self.user_agent}
                r = requests.get(url, headers = header)

            elif statement == "Balance Sheet": #! consider replacing == with list of acceptable values for a .contains + casing = False

                url = xml.query('report_short_name == "BALANCE SHEETS"')['report_url'].tolist()[0]
                
                header = {'User-Agent': self.user_agent}
                r = requests.get(url, headers = header)

            elif statement == "Cash Flow":

                url = xml.query('report_short_name == "CASH FLOWS STATEMENTS"')['report_url'].tolist()[0]
                
                header = {'User-Agent': self.user_agent}
                r = requests.get(url, headers = header)
                print(r)
            
            else:

                raise ValueError
        
        except ValueError:
            text = (
                "Only the following values are accepted:"
                "\tIncome Statement"
                "\tBalance Sheet"
                "\tCash Flow"
            )
            print(text)

        # having received web content, pivot to beautiful soup

        soup = BeautifulSoup(r.content, 'html')

        # parse soup and create dataframe
        parsed_soup = Edgar.__parse_soup(self, soup)
        
        # create dataframe
        df = Edgar.__make_df(self, parsed_soup)
        
        return(df)


# test run of above
msft = Edgar(company = "MSFT", user_agent="test test@test")
msft_10q_20210930_inc_st = msft.get_financial_statement(submission = "000156459021051992",
                                               statement = "Income Statement")
msft_10q_20210930_inc_st.to_csv('out/msft_10q_20210930_inc_st.csv', index = False)