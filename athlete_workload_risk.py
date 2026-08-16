import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


print("=" * 80)
print("        ATHLETE WORKLOAD RISK & TRAINING MONOTONY ANALYZER")
print("=" * 80)


# ------------------------------------------
# Load Data
# ------------------------------------------

data = pd.read_csv(
    "athlete_workload_data.csv"
)

data["Date"] = pd.to_datetime(
    data["Date"]
)

data = data.sort_values(
    ["Athlete", "Date"]
).reset_index(drop=True)


# ------------------------------------------
# Data Validation
# ------------------------------------------

print("\n" + "=" * 80)
print("DATA VALIDATION")
print("=" * 80)

print(f"Rows           : {len(data)}")
print(f"Columns        : {len(data.columns)}")
print(
    f"Missing values : "
    f"{data.isnull().sum().sum()}"
)
print(
    f"Athletes       : "
    f"{data['Athlete'].nunique()}"
)


# ------------------------------------------
# Session Training Load
# ------------------------------------------

data["Training_Load"] = (
    data["Duration_min"]
    *
    data["sRPE"]
)


# ------------------------------------------
# Display Session Data
# ------------------------------------------

print("\n" + "=" * 80)
print("SESSION TRAINING LOAD")
print("=" * 80)

print(
    data[
        [
            "Athlete",
            "Date",
            "Session_Type",
            "Duration_min",
            "sRPE",
            "Training_Load"
        ]
    ].to_string(index=False)
)


# ------------------------------------------
# Week Identification
# ------------------------------------------

data["Week"] = (
    data["Date"]
    .dt.isocalendar()
    .week
    .astype(int)
)


data["Year"] = (
    data["Date"]
    .dt.year
)


data["Week_ID"] = (
    data["Year"].astype(str)
    +
    "-W"
    +
    data["Week"].astype(str).str.zfill(2)
)


# ------------------------------------------
# Weekly Athlete Load
# ------------------------------------------

weekly_load = (
    data.groupby(
        [
            "Athlete",
            "Year",
            "Week",
            "Week_ID"
        ]
    )
    .agg(
        Weekly_Load=(
            "Training_Load",
            "sum"
        ),

        Training_Days=(
            "Date",
            "nunique"
        ),

        Sessions=(
            "Training_Load",
            "count"
        ),

        Average_Daily_Load=(
            "Training_Load",
            "mean"
        ),

        Daily_Load_SD=(
            "Training_Load",
            "std"
        )
    )
    .reset_index()
)


# ------------------------------------------
# Handle Standard Deviation
# ------------------------------------------

weekly_load["Daily_Load_SD"] = (
    weekly_load["Daily_Load_SD"]
    .fillna(0)
)


# ------------------------------------------
# Training Monotony
# ------------------------------------------

weekly_load["Training_Monotony"] = np.where(
    weekly_load["Daily_Load_SD"] > 0,

    (
        weekly_load["Average_Daily_Load"]
        /
        weekly_load["Daily_Load_SD"]
    ),

    0
)


# ------------------------------------------
# Training Strain
# ------------------------------------------

weekly_load["Training_Strain"] = (
    weekly_load["Weekly_Load"]
    *
    weekly_load["Training_Monotony"]
)


# ------------------------------------------
# Previous Week Load
# ------------------------------------------

weekly_load = weekly_load.sort_values(
    [
        "Athlete",
        "Year",
        "Week"
    ]
).reset_index(drop=True)


weekly_load["Previous_Week_Load"] = (
    weekly_load
    .groupby("Athlete")["Weekly_Load"]
    .shift(1)
)


# ------------------------------------------
# Week-to-Week Load Change
# ------------------------------------------

weekly_load["Load_Change_%"] = np.where(
    weekly_load["Previous_Week_Load"] > 0,

    (
        (
            weekly_load["Weekly_Load"]
            -
            weekly_load["Previous_Week_Load"]
        )
        /
        weekly_load["Previous_Week_Load"]
    )
    *
    100,

    0
)


# ------------------------------------------
# Monotony Classification
# ------------------------------------------

def classify_monotony(value):

    if value >= 2.0:
        return "HIGH"

    elif value >= 1.5:
        return "MODERATE"

    else:
        return "LOW"


weekly_load["Monotony_Status"] = (
    weekly_load["Training_Monotony"]
    .apply(classify_monotony)
)


# ------------------------------------------
# Load Change Classification
# ------------------------------------------

def classify_load_change(value):

    absolute_change = abs(value)

    if absolute_change >= 20:
        return "HIGH"

    elif absolute_change >= 10:
        return "MODERATE"

    else:
        return "LOW"


weekly_load["Load_Change_Status"] = (
    weekly_load["Load_Change_%"]
    .apply(classify_load_change)
)


# ------------------------------------------
# Overall Workload Risk
# ------------------------------------------

def calculate_risk(row):

    score = 0

    if row["Monotony_Status"] == "HIGH":
        score += 2

    elif row["Monotony_Status"] == "MODERATE":
        score += 1

    if row["Load_Change_Status"] == "HIGH":
        score += 2

    elif row["Load_Change_Status"] == "MODERATE":
        score += 1

    if row["Training_Strain"] >= 4000:
        score += 2

    elif row["Training_Strain"] >= 2500:
        score += 1

    if score >= 4:
        return "HIGH"

    elif score >= 2:
        return "MODERATE"

    else:
        return "LOW"


weekly_load["Workload_Risk"] = (
    weekly_load.apply(
        calculate_risk,
        axis=1
    )
)


# ------------------------------------------
# Monitoring Recommendation
# ------------------------------------------

def monitoring_recommendation(risk):

    if risk == "HIGH":

        return (
            "Review workload distribution, "
            "recovery and upcoming training."
        )

    elif risk == "MODERATE":

        return (
            "Monitor workload trend and "
            "athlete response."
        )

    else:

        return (
            "Continue normal monitoring."
        )


weekly_load[
    "Monitoring_Recommendation"
] = (
    weekly_load["Workload_Risk"]
    .apply(monitoring_recommendation)
)


# ------------------------------------------
# Weekly Analysis Output
# ------------------------------------------

print("\n" + "=" * 80)
print("WEEKLY WORKLOAD ANALYSIS")
print("=" * 80)

display_columns = [
    "Athlete",
    "Week_ID",
    "Weekly_Load",
    "Training_Days",
    "Sessions",
    "Average_Daily_Load",
    "Daily_Load_SD",
    "Training_Monotony",
    "Training_Strain",
    "Load_Change_%",
    "Monotony_Status",
    "Load_Change_Status",
    "Workload_Risk"
]

display_data = weekly_load[
    display_columns
].copy()


for column in [
    "Weekly_Load",
    "Average_Daily_Load",
    "Daily_Load_SD",
    "Training_Monotony",
    "Training_Strain",
    "Load_Change_%"
]:

    display_data[column] = (
        display_data[column]
        .round(1)
    )


print(
    display_data.to_string(
        index=False
    )
)


# ------------------------------------------
# Athlete Summary
# ------------------------------------------

athlete_summary = (
    weekly_load.groupby("Athlete")
    .agg(
        Total_Weeks=(
            "Week_ID",
            "count"
        ),

        Total_Load=(
            "Weekly_Load",
            "sum"
        ),

        Average_Weekly_Load=(
            "Weekly_Load",
            "mean"
        ),

        Average_Monotony=(
            "Training_Monotony",
            "mean"
        ),

        Average_Strain=(
            "Training_Strain",
            "mean"
        ),

        High_Risk_Weeks=(
            "Workload_Risk",
            lambda x:
            (x == "HIGH").sum()
        ),

        Moderate_Risk_Weeks=(
            "Workload_Risk",
            lambda x:
            (x == "MODERATE").sum()
        )
    )
    .reset_index()
)


print("\n" + "=" * 80)
print("ATHLETE WORKLOAD SUMMARY")
print("=" * 80)

summary_display = athlete_summary.copy()

for column in [
    "Total_Load",
    "Average_Weekly_Load",
    "Average_Monotony",
    "Average_Strain"
]:

    summary_display[column] = (
        summary_display[column]
        .round(1)
    )


print(
    summary_display.to_string(
        index=False
    )
)


# ------------------------------------------
# Highest Risk Weeks
# ------------------------------------------

high_risk = weekly_load[
    weekly_load["Workload_Risk"] == "HIGH"
]


print("\n" + "=" * 80)
print("HIGH WORKLOAD RISK PERIODS")
print("=" * 80)


if high_risk.empty:

    print(
        "No high workload risk periods detected."
    )

else:

    for _, row in high_risk.iterrows():

        print(
            f"{row['Athlete']:<10} "
            f"{row['Week_ID']} | "
            f"Weekly Load: "
            f"{row['Weekly_Load']:.0f} AU | "
            f"Monotony: "
            f"{row['Training_Monotony']:.2f} | "
            f"Strain: "
            f"{row['Training_Strain']:.0f}"
        )


# ------------------------------------------
# Weekly Training Load Plot
# ------------------------------------------

plt.figure(
    figsize=(12, 7)
)

for athlete in weekly_load[
    "Athlete"
].unique():

    athlete_data = weekly_load[
        weekly_load["Athlete"] == athlete
    ]

    plt.plot(
        athlete_data["Week_ID"],
        athlete_data["Weekly_Load"],
        marker="o",
        label=athlete
    )


plt.title(
    "Weekly Athlete Training Load"
)

plt.xlabel("Training Week")

plt.ylabel(
    "Weekly Training Load (AU)"
)

plt.xticks(
    rotation=45
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "weekly_training_load.png",
    dpi=300
)

plt.show()


# ------------------------------------------
# Workload Risk Dashboard
# ------------------------------------------

risk_counts = (
    weekly_load["Workload_Risk"]
    .value_counts()
    .reindex(
        [
            "LOW",
            "MODERATE",
            "HIGH"
        ],
        fill_value=0
    )
)


plt.figure(
    figsize=(8, 6)
)

plt.bar(
    risk_counts.index,
    risk_counts.values
)

plt.title(
    "Workload Risk Distribution"
)

plt.xlabel(
    "Workload Risk"
)

plt.ylabel(
    "Number of Athlete-Weeks"
)

plt.tight_layout()

plt.savefig(
    "workload_risk_dashboard.png",
    dpi=300
)

plt.show()


# ------------------------------------------
# Export Results
# ------------------------------------------

weekly_load.to_csv(
    "workload_risk_results.csv",
    index=False
)


# ------------------------------------------
# Final Output
# ------------------------------------------

print("\n" + "=" * 80)
print("WORKLOAD RISK ANALYSIS COMPLETE")
print("=" * 80)

print("Generated files:")

print(
    "1. workload_risk_results.csv"
)

print(
    "2. weekly_training_load.png"
)

print(
    "3. workload_risk_dashboard.png"
)

print("\n" + "=" * 80)
print(
    "LOAD • MONOTONY • STRAIN • MONITOR"
)
print("=" * 80)