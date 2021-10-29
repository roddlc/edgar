import pandas as pd
import numpy as np
import helper_functions as hf


"""
This script will return a dataframe containing all financial filing information
for a given company. Currently a work in progress (as of 10/28)
"""

def get_company_facts_data(search_val):
    """
    In progress
    """

    # Add request to sec api here
    # return result


def main(search_val, ):
    """
    In progress
    """

    #result =  # will add


    # facts =  # will add


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



# create 