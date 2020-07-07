## Poverty Alleviation and Universal Cash Programs

While[ US GDP per capita has more than doubled in the past 50 years](https://fred.stlouisfed.org/series/A939RX0Q048SBEA), many Americans still remain in poverty. According to the Census Bureau's 2018 Supplemental Poverty Measure (SPM), over 40 million Americans live below their SPM poverty threshold.

While some [large guaranteed-income programs have been shown to nearly eliminate poverty](https://www.ubicenter.org/plans), policymakers should be aware of which programs are best under given spending constraints.  The purpose of this paper is to provide insight on the impact of new universal cash programs on poverty alleviation with varying levels of spending. 

This paper examines the poverty rate impacts of three different universal cash programs: a Child Allowance, which would provide families monthly stipends based on how many children they have, an Adult Universal Basic Income (UBI) which would provide monthly stipends only to adults, and an All UBI which would provide an equal monthly stipend to all Americans regardless of age.

Two years ago, Matt Bruenig produced a similar [paper](https://www.peoplespolicyproject.org/2018/11/29/a-child-allowance-would-be-very-effective-at-poverty-reduction/) using 2017 data in which he compared the same three programs and their impact on the poverty rate up until \\$500 billion in new spending.  Bruenig found that at all levels of spending up to \\$500 billion, a Child Allowance was the most effective program at reducing poverty.  This paper will expand new spending out to \\$1 trillion with updated data from 2018.

## Background
I used data from the Census Bureau’s 2019 Annual Social and Economic Supplement (ASEC), which uses data collected in 2018.  The ASEC survey contains over 180,000 Americans from more than 75,000 households.  Each respondent is assigned a sample weight by the Census Bureau so that models can provide consistent national-level estimates.  

Respondents are determined to be in poverty if their total family income (post tax and transfers) is less than their family poverty threshold.  Poverty thresholds are determined by the Census Bureau using size and age demographics of each family and annual changes in the Consumer Price Index.  

In 2018, 12.7 percent of all Americans were in poverty, including 13.6 percent of children and 12.5 percent of adults.


## Results

Similar to Bruenig's results, I found that a Child Allowance was the most effective at reducing overall poverty up until \\$500 billion.  However, at levels beyond \$500 billion, an All UBI was most effective at dropping the overall poverty rate.

Spending \\$100 billion on a Child Allowance would equate to monthly stipends of \\$114 per child and lift 4.5 million Americans out of poverty.  \\$500 billion on either a Child Allowance or All UBI would lift 12 million Americans out of poverty.  Spending $1 trillion on an All UBI would equate to monthly checks of \\$258 per American and lift over 22 million people out of poverty.

The interactive graph below shows the poverty impacts of each program at different funding levels.


import pandas as pd
import numpy as np
import plotly.express as px
import plotly

person_raw = pd.read_csv('https://github.com/MaxGhenis/datarepo/raw/master/pppub19.csv.gz',
                         usecols=['MARSUPWT', 'SPM_ID', 'SPM_POVTHRESHOLD',
                                  'SPM_RESOURCES', 'A_AGE','ACTC_CRD', 'PEMLR',
                                  'PRDTRACE', 'PRCITSHP', 'PEHSPNON'])

person = person_raw.copy(deep=True)

person.columns = person.columns.str.lower()
person['weight'] = person.marsupwt/100
person['child'] = person.a_age < 18
person['adult'] = person.a_age >= 18
spmu_ages = person.groupby('spm_id')[['child','adult']].sum()
spmu_ages.columns = ['children', 'total_adults']
person2 = person.merge(spmu_ages,left_on='spm_id', right_index=True)
total_children = (person2.child * person2.weight).sum()
total_adults = (person2.adult * person2.weight).sum()

child_allowance_overall = []
child_allowance_child = []
child_allowance_adults = []

for spending in range(0, 1000000000001, 50000000000):
    child_allowance_per_child = spending/total_children
    total_child_allowance = person2.children * child_allowance_per_child
    new_spm_resources_ca = person2.spm_resources + total_child_allowance
    new_poor_ca = new_spm_resources_ca < person2.spm_povthreshold
    new_total_child_poor = ((person2.child * person2.weight * 
                             new_poor_ca).sum())
    new_child_poverty_rate = ((new_total_child_poor)/
                              (person2.child * person2.weight).sum())
    new_total_adult_poor = ((person2.adult * person2.weight * 
                             new_poor_ca).sum())
    new_adult_poverty_rate = ((new_total_adult_poor)/
                              (person2.adult * person2.weight).sum())
    new_total_poor_ca = (new_poor_ca * person2.weight).sum()
    new_poverty_rate_ca = new_total_poor_ca/person2.weight.sum()
    child_allowance_overall.append(new_poverty_rate_ca)
    child_allowance_child.append(new_child_poverty_rate)
    child_allowance_adults.append(new_adult_poverty_rate)
    
ubi_adults_overall = []
ubi_adults_child = []
ubi_adults_adults = []

for spending in range(0, 1000000000001, 50000000000):
    adult_ubi = spending/total_adults
    total_adult_ubi = person2.total_adults * adult_ubi
    new_spm_resources_ubi = person2.spm_resources + total_adult_ubi
    new_poor_ubi = new_spm_resources_ubi < person2.spm_povthreshold
    new_total_child_poor = ((person2.child * person2.weight * 
                             new_poor_ubi).sum())
    new_child_poverty_rate = ((new_total_child_poor)/
                              (person2.child * person2.weight).sum())
    new_total_adult_poor = ((person2.adult * person2.weight * 
                             new_poor_ubi).sum())
    new_adult_poverty_rate = ((new_total_adult_poor)/
                              (person2.adult * person2.weight).sum())
    new_total_poor_ubi = (new_poor_ubi * person2.weight).sum()
    new_poverty_rate_ubi = new_total_poor_ubi/person2.weight.sum()
    ubi_adults_overall.append(new_poverty_rate_ubi)
    ubi_adults_child.append(new_child_poverty_rate)
    ubi_adults_adults.append(new_adult_poverty_rate)
    
ubi_all_overall = []
ubi_all_child = []
ubi_all_adults = []

for spending in range(0, 1000000000001, 50000000000):
    all_ubi_per_person = spending/(total_adults + total_children)
    total_all_ubi = ((person2.children * all_ubi_per_person) + 
                    (person2.total_adults * all_ubi_per_person))
    new_spm_resources_all_ubi = person2.spm_resources + total_all_ubi
    new_poor_all_ubi = new_spm_resources_all_ubi < person2.spm_povthreshold
    new_total_child_poor = ((person2.child * person2.weight * 
                             new_poor_all_ubi).sum())
    new_child_poverty_rate = ((new_total_child_poor)/
                              (person2.child * person2.weight).sum())
    new_total_adult_poor = ((person2.adult * person2.weight * 
                             new_poor_all_ubi).sum())
    new_adult_poverty_rate = ((new_total_adult_poor)/
                              (person2.adult * person2.weight).sum())
    new_total_poor_all_ubi = (new_poor_all_ubi * person2.weight).sum()
    new_poverty_rate_all_ubi = new_total_poor_all_ubi/person2.weight.sum()
    ubi_all_overall.append(new_poverty_rate_all_ubi)
    ubi_all_child.append(new_child_poverty_rate)
    ubi_all_adults.append(new_adult_poverty_rate)
    
spending_data = []
for spending in range(0, 1001, 50):
    spending = spending/100
    spending_data.append(spending)
    
    
overall = {'spending_in_billions': spending_data,
                     'child_allowance': child_allowance_overall,
                     'adult_ubi': ubi_adults_overall,
                     'all_ubi': ubi_all_overall}
                    

overall_df = pd.DataFrame(overall)
overall_df = pd.DataFrame(overall_df).round(3)

child = {'spending_in_billions': spending_data,
                     'child_allowance': child_allowance_child,
                     'adult_ubi': ubi_adults_child,
                     'all_ubi': ubi_all_child}
                    

child_df = pd.DataFrame(child)
child_df = pd.DataFrame(child_df).round(3)

adult = {'spending_in_billions': spending_data,
                     'child_allowance': child_allowance_adults,
                     'adult_ubi': ubi_adults_adults,
                     'all_ubi': ubi_all_adults}
                    

adult_df = pd.DataFrame(adult)
adult_df = pd.DataFrame(adult_df).round(3)

program = (pd.melt(overall_df, 'spending_in_billions', 
                   var_name='ubi_type',value_name='poverty_rate'))
program.poverty_rate *= 100
program['ubi_type'] = (np.where(program['ubi_type'] == 'child_allowance', 
                                'Child Allowance', np.where(program['ubi_type']
                                     == 'adult_ubi', 'Adult UBI', 'All UBI')))

def melt_dict(d):
  """ prdouce long version of data frame represented by dictionary (d)
  """
  df = pd.DataFrame(d).round(3) * 100
  program = pd.melt(df, 'spending_in_billions', var_name='ubi_type',value_name='poverty_rate')
  program['ubi_type'] = np.where(program['ubi_type'] == 'child_allowance', 'Child Allowance', 
                                 np.where(program['ubi_type'] == 'adult_ubi', 'Adult UBI', 'All UBI'))
  
  # could use pd.replace function
  return program

program_overall = melt_dict(overall)
program_child = melt_dict(child)
program_adult = melt_dict(adult)

def line_graph(df, x, y, color, title, xaxis_title, yaxis_title):
    fig = px.line(df, x=x, y=y, color=color)
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        yaxis_ticksuffix='%',
        font=dict(family='Roboto'),
        hovermode='x',
        legend_title_text=''
        
    )

    fig.update_traces(mode='markers+lines', hovertemplate=None)

    fig.show()

line_graph(df=program_overall, x='spending_in_billions', 
           y='poverty_rate', color='ubi_type',
           title='Overall Poverty Rate and Spending on Cash Transfer Programs',
           xaxis_title='Spending in Billions',
           yaxis_title='Poverty Rate')

Unsurprisingly, a Child Allowance was the most effective program at reducing child poverty at all levels of spending.  Spending \\$400 billion on a Child Allowance cuts child poverty by over two-thirds, from 13.6% to 4.3%

Comparatively, spending $1 trillion on an Adult UBI leaves 7% of children still in poverty. For an All UBI and a Child Allowance under the same spending, 4% and 1% of children would remain in poverty respectively. 


line_graph(df=program_child, x='spending_in_billions', 
           y='poverty_rate', color='ubi_type',
           title='Child Poverty Rate and Spending on Cash Transfer Programs',
           xaxis_title='Spending in Billions',
           yaxis_title='Child Poverty Rate')

An Adult UBI and an All UBI have nearly identical effects on the adult poverty rate. A Child Allowance has a smaller impact on adult poverty because the benefits only go to adults with children in their family.

line_graph(df=program_adult, x='spending_in_billions', 
           y='poverty_rate', color='ubi_type',
           title='Adult Poverty Rate and Spending on Cash Transfer Programs',
           xaxis_title='Spending in Billions',
           yaxis_title='Adult Poverty Rate')

## Conclusion

The results of this paper detail the importance of including children in universal cash transfer programs.  At all funding levels, UBIs that exclude children are less efficient than child allowances and full UBIs for reducing poverty.   Additionally, policy makers and advocates should be aware that different spending constraints should influence the specific universal cash program enacted.  

Given limited political support for added spending, a Child Allowance is the most effective way to alleviate poverty quickly.  If the political appetite for poverty reduction is more substantial, policy makers should aim to provide a truly universal UBI and provide cash transfers to everyone.
