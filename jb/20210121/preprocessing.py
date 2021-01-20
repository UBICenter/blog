import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import microdf as mdf

person = pd.read_csv(
    "https://github.com/MaxGhenis/datarepo/raw/master/pppub20.csv.gz",
    usecols=[
        "MARSUPWT",
        "SPM_ID",
        "SPM_POVTHRESHOLD",
        "SPM_RESOURCES",
        "A_AGE",
        "TAX_INC",
        "SPM_WEIGHT",
        "SPM_NUMPER",
    ],
)

# Lower column headers and adapt weights
person.columns = person.columns.str.lower()
person["person_weight"] = person.marsupwt / 100
person.spm_weight /= 100

# Determine age demographic
person["child"] = person.a_age < 18
person["adult"] = person.a_age > 17

# calculate population statistics
adult_pop = (person.adult * person.person_weight).sum()
child_pop = (person.child * person.person_weight).sum()
pop = child_pop + adult_pop

# Create SPMU dataframe
spmu = (
    person.groupby(
        [
            "spm_id",
            "spm_weight",
            "spm_povthreshold",
            "spm_resources",
            "spm_numper",
        ]
    )[["child", "adult", "tax_inc"]]
    .sum()
    .reset_index()
)

total_taxable_income = (spmu.tax_inc * spmu.spm_weight).sum()


def pov_gap(df, resources, threshold, weight):
    gaps = np.maximum(df[threshold] - df[resources], 0)
    return (gaps * df[weight]).sum()


def ubi(
    funding_billions=0, child_percent_funding=None, child_percent_ubi=None
):
    """
    args:
        funding_billions: total annual funding for UBI program in billions USD
        child_percent_funding: percent (in whole numbers) of annual funds earmarked
        for child beneficiaries
        child_percent_ubi: proportion of child beneficiary's UBI benefit compared to adult
        beneficiary's payment

    returns:
        series of elements:
         poverty_rate: headcount poverty rate using Supplemental Poverty Measure threshold
         gini: gini coefficient of income
         poverty_gap: SPM unit poverty gap
         percent_better_off: percent of population with higher income after new transfers and taxes
         adult_ubi: annual per adult benefit in dollars
         child_ubi: annual per adult benefit in dollars
    """
    funding = funding_billions * 1e9

    if child_percent_funding is not None:
        child_percent_funding /= 100
        adult_ubi = ((1 - child_percent_funding) * funding) / adult_pop
        child_ubi = (child_percent_funding * funding) / child_pop
    else:
        child_percent_ubi /= 100
        adult_ubi = funding / (adult_pop + (child_pop * child_percent_ubi))
        child_ubi = adult_ubi * child_percent_ubi

    tax_rate = funding / total_taxable_income

    spmu["new_tax"] = tax_rate * spmu.tax_inc
    spmu["spm_ubi"] = (spmu.child * child_ubi) + (spmu.adult * adult_ubi)

    spmu["new_spm_resources"] = (
        spmu.spm_resources + spmu.spm_ubi - spmu.new_tax
    )
    spmu["new_spm_resources_pp"] = spmu.new_spm_resources / spmu.spm_numper

    # Calculate poverty gap
    poverty_gap = pov_gap(
        spmu, "new_spm_resources", "spm_povthreshold", "spm_weight"
    )

    # Merge person and spmu dataframes
    spmu_sub = spmu[["spm_id", "new_spm_resources", "new_spm_resources_pp"]]
    target_persons = pd.merge(spmu_sub, person, on=["spm_id"])

    target_persons["poor"] = (
        target_persons.new_spm_resources < target_persons.spm_povthreshold
    )
    total_poor = (target_persons.poor * target_persons.person_weight).sum()
    poverty_rate = total_poor / pop * 100

    # Calculate Gini
    gini = mdf.gini(target_persons, "new_spm_resources_pp", w="person_weight")

    # Percent winners
    target_persons["better_off"] = (
        target_persons.new_spm_resources > target_persons.spm_resources
    )
    total_better_off = (
        target_persons.better_off * target_persons.person_weight
    ).sum()
    percent_better_off = total_better_off / pop

    return pd.Series(
        {
            "poverty_rate": poverty_rate,
            "gini": gini,
            "poverty_gap": poverty_gap,
            "percent_better_off": percent_better_off,
            "adult_ubi": adult_ubi,
            "child_ubi": child_ubi,
        }
    )


# create a dataframe with all possible combinations of funding levels and
summary = mdf.cartesian_product(
    {
        "funding_billions": np.arange(0, 3_001, 50),
        "child_percent_funding": np.arange(0, 101, 1),
    }
)


def ubi_row(row):
    return ubi(
        funding_billions=row.funding_billions,
        child_percent_funding=row.child_percent_funding,
    )


summary[
    [
        "poverty_rate",
        "gini",
        "poverty_gap",
        "percent_better_off",
        "adult_ubi",
        "child_ubi",
    ]
] = summary.apply(ubi_row, axis=1)

summary["monthly_child_ubi"] = summary["child_ubi"].apply(
    lambda x: int(round(x / 12, 0))
)
summary["monthly_adult_ubi"] = summary["adult_ubi"].apply(
    lambda x: int(round(x / 12, 0))
)


# drop rows where funding level is 0, it adds unnecessary noise to graphs
def get_top(col):
    res = summary.sort_values(col).drop_duplicates(
        "funding_billions", keep="first"
    )
    return res[res.funding_billions > 0]


optimal_poverty = get_top("poverty_gap")
optimal_inequality = get_top("gini")
optimal_winners = get_top("percent_better_off")

# write df to csv
summary.to_csv("children_share_funding_summary.csv.gz", compression="gzip")

summary2 = mdf.cartesian_product(
    {
        "funding_billions": np.arange(0, 3_001, 50),
        "child_percent_ubi": np.arange(0, 101, 50),
    }
)


def big_percent_row(row):
    return ubi(
        funding_billions=row.funding_billions,
        child_percent_ubi=row.child_percent_ubi,
    )


summary2[
    [
        "poverty_rate",
        "gini",
        "poverty_gap",
        "percent_better_off",
        "adult_ubi",
        "child_ubi",
    ]
] = summary2.apply(big_percent_row, axis=1)

# calculate monthly payments
summary2["monthly_child_ubi"] = summary2["child_ubi"].apply(
    lambda x: int(round(x / 12, 0))
)
summary2["monthly_adult_ubi"] = summary2["adult_ubi"].apply(
    lambda x: int(round(x / 12, 0))
)

summary2.to_csv("children_share_ubi_summary.csv.gz", compression="gzip")
