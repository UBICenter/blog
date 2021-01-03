# -*- coding: utf-8 -*-
"""Percent - How much should a child get?

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MXNFC_ClLnHFupipXG618P39Tunavn7C
    graphs removed
    

"""

## To Do ##
# use hovertemplate to add labels for Adult UBI, Child UBI, and Ratio
# Chart that shows the current state of child poverty?
# Make a chart about child poverty, kids get 0, half, all

# Install microdf
# !pip install git+https://github.com/PSLmodels/microdf.git
# # update plotly
# !pip install plotly --upgrade

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import microdf as mdf

person = pd.read_csv('https://github.com/MaxGhenis/datarepo/raw/master/pppub20.csv.gz',
                     usecols=['MARSUPWT', 'SPM_ID', 'SPM_POVTHRESHOLD',
                                  'SPM_RESOURCES','A_AGE', 'TAX_INC'])

# Lower column headers and adapt weights
person.columns = person.columns.str.lower()
person['weight'] = person.marsupwt / 100

# Determine age demographic
person['child'] = person.a_age < 18
person['adult'] = person.a_age > 17

# Calculate the number of children and adults in each household
households = person.groupby(['spm_id'])[['child','adult', 'tax_inc']].sum()
households.columns = ['hh_children', 'hh_adults', 'hh_tax_income']
person = person.merge(households,left_on=['spm_id'], right_index=True)
person['hh_total_people'] = person.hh_adults + person.hh_children

# calculate population statistics
adult_pop = (person.adult * person.weight).sum()
child_pop = (person.child * person.weight).sum()
pop = child_pop + adult_pop
child_pop / pop

# calculate the total taxable income of the population
total_taxable_income = (person.tax_inc * person.weight).sum()




def ubi(funding_billions=0, percent=0):
  """ Calculate the poverty rate among the total US population by:
  
  -passing a total level of funding for a UBI proposal (billions USD),
  -passing a percent of the benefit recieved by a child and the benefit
  recieved by an adult
  AND
  taking into account that funding will be raise by a flat tax leveled on each households
  taxable income """

  percent = percent / 100

  funding = funding_billions * 1e9

  target_persons = person.copy(deep=True)

  # i think this is % funding, not % benefit
  adult_ubi = ((1 - percent) * funding) / adult_pop
  child_ubi = (percent * funding) / child_pop

  tax_rate = funding / total_taxable_income

  target_persons['hh_new_tax'] = target_persons.hh_tax_income * tax_rate

  target_persons['hh_ubi'] = (target_persons.hh_adults * adult_ubi + 
                              target_persons.hh_children * child_ubi)
  
  target_persons['new_spm_resources'] = (target_persons.spm_resources + 
                                         target_persons.hh_ubi -
                                         target_persons.hh_new_tax)
  
  target_persons['new_spm_resources_pp'] = (target_persons.new_spm_resources / 
                                            (target_persons.hh_total_people))

  
  # Calculate poverty rate
  target_persons['poor'] = (target_persons.new_spm_resources < 
                            target_persons.spm_povthreshold)
  
  total_poor = (target_persons.poor * target_persons.weight).sum()
  poverty_rate = (total_poor / pop * 100)

  # Calculate poverty gap
  target_persons['poverty_gap'] = target_persons.spm_povthreshold - target_persons.new_spm_resources
  spmu=target_persons.drop_duplicates(subset='spm_id')

  poverty_gap = (((spmu.poor * spmu.poverty_gap
                             * spmu.weight).sum()))

  # Calculate Gini
  gini = mdf.gini(target_persons, 'new_spm_resources_pp', w='weight')

  # Percent winners
  target_persons['better_off'] = (target_persons.new_spm_resources > target_persons.spm_resources)
  total_better_off = (target_persons.better_off * target_persons.weight).sum()
  percent_better_off = total_better_off / pop

  return pd.Series([poverty_rate, gini, poverty_gap, percent_better_off, adult_ubi, child_ubi])

# create a dataframe with all possible combinations of funding levels and
summary = mdf.cartesian_product({'funding_billions': np.arange(0,3_001,50),
                                 'percent': np.arange(0, 101, 1)})

def ubi_row(row):  
    return ubi(row.funding_billions, row.percent)
summary[['poverty_rate', 'gini', 'poverty_gap', 'percent_better_off', 'adult_ubi', 'child_ubi']] = summary.apply(ubi_row, axis=1)

summary.sample(5)

"""## Save `summary` to CSV"""

summary['monthly_child_ubi'] =summary['child_ubi'].apply(lambda x: int(round(x/12,0)))
summary['monthly_adult_ubi'] =summary['adult_ubi'].apply(lambda x: int(round(x/12,0)))
summary.to_csv("children_share_ubi_spending_summary.csv.gz",compression='gzip')

"""## `optimal_[whatever concept]` `dataframe`s for `ubi()` """

# drop rows where funding level is 0
optimal_poverty = summary.sort_values('poverty_gap').drop_duplicates('funding_billions', keep='first')
optimal_poverty = optimal_poverty.drop(
    optimal_poverty[optimal_poverty.funding_billions==0].index
    ) 

optimal_inequality = summary.sort_values('gini').drop_duplicates('funding_billions', keep='first')
optimal_inequality = optimal_inequality.drop(
    optimal_inequality[optimal_inequality.funding_billions==0].index
    ) 

optimal_winners = summary.sort_values('percent_better_off').drop_duplicates('funding_billions', keep='last')
optimal_winners = optimal_winners.drop(
    optimal_winners[optimal_winners.funding_billions==0].index
    ) 



"""# `big_percent()` function"""

def big_percent(funding_billions=0, percent=1000):
  """ Calculate the poverty rate among the total US population by:
  
  -passing a total level of funding for a UBI proposal (billions USD),
  -passing a percent of the benefit recieved by a child and the benefit
  recieved by an adult
  AND
  taking into account that funding will be raise by a flat tax leveled on each households
  taxable income """

  percent = percent / 100

  funding = funding_billions * 1e9

  target_persons = person.copy(deep=True)
  adult_ubi = (funding / (adult_pop + (child_pop * percent)))
  child_ubi = adult_ubi * percent

  tax_rate = funding / total_taxable_income

  target_persons['hh_new_tax'] = target_persons.hh_tax_income * tax_rate

  target_persons['hh_ubi'] = (target_persons.hh_adults * adult_ubi + 
                              target_persons.hh_children * child_ubi)
  
  target_persons['new_spm_resources'] = (target_persons.spm_resources + 
                                         target_persons.hh_ubi -
                                         target_persons.hh_new_tax)
  
  target_persons['new_spm_resources_pp'] = (target_persons.new_spm_resources / 
                                            (target_persons.hh_total_people))

  
  # Calculate poverty rate
  target_persons['poor'] = (target_persons.new_spm_resources < 
                            target_persons.spm_povthreshold)
  
  total_child_poor = (target_persons.poor * target_persons.weight * 
                      target_persons.child).sum()
  child_poverty_rate = (total_child_poor / child_pop * 100).round(1)

  adult_ubi = int(adult_ubi)
  child_ubi = int(child_ubi)

  return pd.Series([child_poverty_rate, adult_ubi, child_ubi])

summary2 = mdf.cartesian_product({'funding_billions': np.arange(0,3_001,50),
                                 'percent': np.arange(0, 101, 50)})

def big_percent_row(row):  
    return big_percent(row.funding_billions, row.percent)

summary2[['child_poverty_rate', 'adult_ubi', 'child_ubi']] = summary2.apply(big_percent_row, axis=1)
summary2

# calculate monthly payments
summary2['monthly_child_ubi'] =summary2['child_ubi'].apply(lambda x: int(round(x/12,0)))
summary2['monthly_adult_ubi'] =summary2['adult_ubi'].apply(lambda x: int(round(x/12,0)))

"""## Write `summary2` to CSV"""
summary2.to_csv("ratio_child_ben_to_adult_ben_summary.csv.gz",compression="gzip")
summary2.sample(10)
