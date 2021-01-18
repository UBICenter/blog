import pandas as pd
import numpy as np
import microdf as mdf

person = pd.read_csv(
    "https://github.com/MaxGhenis/datarepo/raw/master/pppub20.csv.gz",
    usecols=[
        "MARSUPWT",
        "SPM_ID",
        "SPM_POVTHRESHOLD",
        "SPM_RESOURCES",
        "SPM_WEIGHT",
        "AGI",
        "FEDTAX_AC",
        "FICA",
    ],
)

# Lower column headers and adapt weights.
person.columns = person.columns.str.lower()
person.marsupwt /= 100
person.spm_weight /= 100
person["person"] = 1
person["fica_fedtax_ac"] = person.fica + person.fedtax_ac

# Calculate the number of children and adults in each household.
SPM_COLS = ["spm_id", "spm_povthreshold", "spm_resources", "spm_weight"]
spmu = person.groupby(SPM_COLS)[["agi", "fica_fedtax_ac", "person"]].sum()
spmu.columns = ["spmu_agi", "spmu_fica_fedtax_ac", "spmu_total_people"]
spmu.reset_index(inplace=True)
spmu["spm_resources_before_tax"] = spmu.spm_resources + spmu.spmu_fica_fedtax_ac
person = person.merge(spmu, on=SPM_COLS)

# Calculate totals at both person and SPM unit levels so we can compare and
# calculate poverty gaps.
person_totals = mdf.weighted_sum(person, ["fica_fedtax_ac", "person"], "marsupwt")

spmu_totals = mdf.weighted_sum(
    spmu, ["spmu_fica_fedtax_ac", "spmu_total_people"], "spm_weight"
)
spmu_totals.index = person_totals.index

totals = pd.concat([person_totals, spmu_totals], axis=1).T
totals.index = ["person", "spmu"]

# Calculate status quo
person["poor"] = person.spm_resources < person.spm_povthreshold
initial_poverty_rate = mdf.weighted_mean(person, "poor", "marsupwt")

spmu["initial_poverty_gap"] = np.maximum(spmu.spm_povthreshold - spmu.spm_resources, 0)
initial_poverty_gap = (spmu.initial_poverty_gap * spmu.spm_weight).sum()

person["spm_resources_pp"] = person.spm_resources / person.spmu_total_people
initial_gini = mdf.gini(person, "spm_resources_pp", w="marsupwt")


def chg(new, base):
    return (100 * (new - base) / base).round(1)


def tax(flat_tax, total_type="person"):
    """Calculate all metrics given a flat tax.

    Args:
        flat_tax: Percentage tax rate (0-100).
        total_type: Whether to use total population and current tax liability
            from SPM units or persons. Either "person" or "spmu".
            Defaults to "person".
    """
    flat_tax /= 100
    spmu["new_tax"] = spmu.spmu_agi * flat_tax
    new_revenue = mdf.weighted_sum(spmu, "new_tax", "spm_weight")
    change_revenue = new_revenue - totals.loc[total_type].fica_fedtax_ac
    ubi = change_revenue / totals.loc[total_type].person

    spmu["new_spm_resources"] = (
        spmu.spm_resources_before_tax + ubi * spmu.spmu_total_people - spmu.new_tax
    )

    # Merge back to each person.
    target_persons = person.merge(spmu[SPM_COLS + ["new_spm_resources"]], on=SPM_COLS)

    target_persons["new_spm_resources_pp"] = (
        target_persons.new_spm_resources / target_persons.spmu_total_people
    )

    # Calculate poverty rate
    target_persons["new_poor"] = (
        target_persons.new_spm_resources < target_persons.spm_povthreshold
    )

    poverty_rate = mdf.weighted_mean(target_persons, "new_poor", "marsupwt")
    change_poverty_rate = chg(poverty_rate, initial_poverty_rate)

    # Calculate poverty gap
    poverty_gaps = np.maximum(spmu.spm_povthreshold - spmu.new_spm_resources, 0)
    poverty_gap = (poverty_gaps * spmu.spm_weight).sum()
    change_poverty_gap = chg(poverty_gap, initial_poverty_gap)

    # Calculate Gini
    gini = mdf.gini(target_persons, "new_spm_resources_pp", w="marsupwt")
    change_gini = chg(gini, initial_gini)

    # Percent winners
    target_persons["better_off"] = (
        target_persons.new_spm_resources > target_persons.spm_resources
    )
    percent_better_off = mdf.weighted_mean(target_persons, "better_off", "marsupwt")

    return pd.Series(
        {
            "poverty_rate": poverty_rate,
            "poverty_gap": poverty_gap,
            "gini": gini,
            "percent_better_off": percent_better_off,
            "change_poverty_rate": change_poverty_rate,
            "change_poverty_gap": change_poverty_gap,
            "change_gini": change_gini,
            "change_revenue": change_revenue,
            "ubi": ubi,
        }
    )


# Construct summary for each flat tax rate.
summary = {"flat_tax": np.arange(0, 51, 1)}
summary = pd.DataFrame(summary)


def tax_row(row):
    return tax(row.flat_tax)


summary = pd.concat([summary, summary.apply(tax_row, axis=1)], axis=1)

summary["poverty_gap_billions"] = (summary.poverty_gap / 1e9).round(1)

summary.gini = summary.gini.round(3)
summary.poverty_rate *= 100
summary.percent_better_off *= 100

summary.to_csv("summary.csv", index=False)
