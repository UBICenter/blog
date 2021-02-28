import pandas as pd
import numpy as np
import microdf as mdf
import scf

s_raw = scf.load(2019, ["networth", "race", "famstruct", "kids", "income"])
s = s_raw.copy(deep=True)
# code races
s["race2"] = np.where(
    s.race.isin([1]),
    "White",  # Not Including Hispanic.
    np.where(s.race == 2, "Black", np.where(s.race == 3, "Hispanic", "Other")),
)

# famstruct 4 and 5 indicate married/LWP (living with partner)
s["numper"] = 1 + s.famstruct.isin([4, 5]) + s.kids
s["adults"] = 1 + s.famstruct.isin([4, 5])

# divide by number of adults
s["networth_pa"] = s.networth / (1 + s.famstruct.isin([4, 5]))

# Calculate tax base by finding weighted sum of individuals and their income.
totals = mdf.weighted_sum(s, ["numper", "income"], w="wgt")
totals.white_hhs = s[s.race2 == "White"].wgt.sum()
totals.black_hhs = s[s.race2 == "Black"].wgt.sum()
totals.total_hhs = s.wgt.sum()


def ubi_sim(data, max_monthly_payment, step_size):
    # Initialize empty list to store our results.
    l = []

    # loop through ubi
    for monthly_payment in np.arange(0, max_monthly_payment + 1, step_size):
        # multiply monthly payment by 12 to get annual payment size
        annual_payment = monthly_payment * 12

        # calculate simulation-level stats
        sim_data = data.copy(deep=True)
        ubi_total = annual_payment * totals.numper
        tax_rate = ubi_total / totals.income
        sim_data["tax_rate"] = tax_rate
        sim_data["ubi_mo"] = monthly_payment
        sim_data["annual_payment"] = annual_payment
        sim_data["networth_new"] = (
            sim_data.networth
            + (annual_payment * sim_data.numper)
            - tax_rate * sim_data.income
        )
        sim_data["networth_pa_new"] = sim_data.networth_new / sim_data.adults
        l.append(sim_data)
    # Return the DataFrames together.
    return pd.concat(l)


# Run the simulation
simulated = ubi_sim(s, 2000, 100)

# create empty list to store candidates for D-statistics
lins = np.array([])
for i in range(4, 6):  # range(2, 9):
    increment = 10 ** (i - 2)
    tmp = np.unique(
        np.round(np.arange(10 ** i, 10 ** (i + 1), increment * 5), -2)
    )
    lins = np.concatenate([lins, tmp])


def shares_below_thresh(data, white_data, black_data, thresh):
    return pd.Series(
        {
            "white_share": white_data[
                white_data.networth_pa_new < thresh
            ].wgt.sum()
            / totals.white_hhs,
            "black_share": black_data[
                black_data.networth_pa_new < thresh
            ].wgt.sum()
            / totals.black_hhs,
            "total_share": data[data.networth_pa_new < thresh].wgt.sum()
            / totals.total_hhs,
        }
    )


cdf_list = []
for step in simulated.ubi_mo.unique():
    data = simulated[simulated.ubi_mo == step]
    white_data = data[data.race2 == "White"]
    black_data = data[data.race2 == "Black"]
    # create df generating networths evenly spaced when we view in log form
    cdf = pd.DataFrame({"networth_pa_new": lins, "ubi_mo": step})
    cdf = pd.concat(
        [
            cdf,
            cdf.networth_pa_new.apply(
                lambda x: shares_below_thresh(data, white_data, black_data, x)
            ),
        ],
        axis=1,
    )
    cdf["d_stat_cand"] = cdf.black_share - cdf.white_share
    cdf_list.append(cdf)

cdfs = pd.concat(cdf_list)

# Create DataFrame summarized at the UBI amount, with columns for:
# - d_stat and associated net worth
# - median and mean net worth by white/black
# - share with net worth above $50k by white/black
cdfs_max = (
    cdfs.sort_values("d_stat_cand", ascending=False).groupby("ubi_mo").head(1)
)
ubi_summary = (
    simulated.groupby("ubi_mo")
    .apply(
        lambda x: pd.Series(
            {
                "black_median_networth_pa": mdf.weighted_median(
                    x[x.race2 == "Black"], "networth_pa_new", "wgt"
                ),
                "white_median_networth_pa": mdf.weighted_median(
                    x[x.race2 == "White"], "networth_pa_new", "wgt"
                ),
                "black_mean_networth_pa": mdf.weighted_median(
                    x[x.race2 == "Black"], "networth_pa_new", "wgt"
                ),
                "white_mean_networth_pa": mdf.weighted_median(
                    x[x.race2 == "White"], "networth_pa_new", "wgt"
                ),
                "black_share_above_50k": x[
                    (x.race2 == "Black") & (x.networth_pa_new >= 50000)
                ].wgt.sum()
                / totals.black_hhs,
                "white_share_above_50k": x[
                    (x.race2 == "White") & (x.networth_pa_new >= 50000)
                ].wgt.sum()
                / totals.white_hhs,
            }
        )
    )
    .reset_index()
)
ubi_summary["white_mean_nw_as_pct_of_mean_black"] = (
    ubi_summary.white_mean_networth_pa / ubi_summary.black_mean_networth_pa
)
ubi_summary["white_median_nw_as_pct_of_median_black"] = (
    ubi_summary.white_median_networth_pa / ubi_summary.black_median_networth_pa
)
ubi_summary["white_share_above_50k_pct_of__black"] = (
    ubi_summary.white_share_above_50k / ubi_summary.black_share_above_50k
)

ubi_summary = ubi_summary.merge(cdfs_max, on="ubi_mo").reset_index()

cdfs.to_csv("cdfs.csv", index=False)
ubi_summary.to_csv("ubi_summary.csv", index=False)
