"""
Freelancing Income & Skill Demand Analytics
Flow: Data -> Preprocessing -> EDA -> Feature Engineering -> Visualization -> Linear Regression -> Prediction
Every number shown on the website is calculated from data/freelancing_data.csv.
"""
import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

app = Flask(__name__)
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "freelancing_data.csv")

# Simple mappings used to encode text columns as numbers
EXPERIENCE_MAP = {"Beginner": 0, "Intermediate": 1, "Expert": 2}
DEMAND_MAP = {"Low": 1, "Medium": 2, "High": 3}
NUMERIC_COLS = ["Projects_Completed", "Hourly_Rate", "Hours_Per_Week", "Client_Rating", "Monthly_Income"]
TEXT_COLS = ["Skill", "Category", "Experience_Level", "Location", "Job_Demand"]
# Input features of the Linear Regression model
FEATURES = ["Experience_Code", "Hourly_Rate", "Hours_Per_Week", "Projects_Completed", "Client_Rating"]


# ---------------------------------------------------------------
# 1. DATA PREPROCESSING + FEATURE ENGINEERING
# ---------------------------------------------------------------
def load_and_clean_data():
    df = pd.read_csv(CSV_PATH)
    report = {"rows_before": len(df), "missing_before": int(df.isnull().sum().sum())}

    df = df.drop_duplicates()                                   # remove duplicate rows
    report["duplicates_removed"] = report["rows_before"] - len(df)

    for col in NUMERIC_COLS:                                    # make sure numbers are numbers
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())              # missing numbers -> median
    for col in TEXT_COLS:
        df[col] = df[col].fillna(df[col].mode()[0])            # missing text -> most common value

    # Encoding: convert categories to numbers
    df["Experience_Code"] = df["Experience_Level"].map(EXPERIENCE_MAP)
    df["Demand_Code"] = df["Job_Demand"].map(DEMAND_MAP)

    # Feature engineering: two simple new columns
    df["Weekly_Income_Est"] = df["Hourly_Rate"] * df["Hours_Per_Week"]
    df["Annual_Income"] = df["Monthly_Income"] * 12

    report["missing_after"] = int(df.isnull().sum().sum())
    report["rows_after"] = len(df)
    return df, report


# ---------------------------------------------------------------
# 2. MACHINE LEARNING: Linear Regression (80% train / 20% test)
# ---------------------------------------------------------------
def train_model(df):
    X = df[FEATURES]
    y = df["Monthly_Income"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    metrics = {
        "r2": round(r2_score(y_test, predictions), 3),
        "mae": round(mean_absolute_error(y_test, predictions)),
        "train_size": len(X_train),
        "test_size": len(X_test),
    }
    return model, metrics


df, prep_report = load_and_clean_data()
model, model_metrics = train_model(df)


# ---------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------
@app.template_filter("inr")
def inr(value):
    """Format a number as Indian Rupees, e.g. 123456 -> ₹1,23,456"""
    s = str(int(round(value)))
    if len(s) > 3:
        last3, rest = s[-3:], s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        s = ",".join(parts + [last3])
    return "₹" + s


def demand_label(score):
    """Convert average demand score (1 to 3) into Low / Medium / High"""
    if score >= 2.34:
        return "High"
    if score >= 1.67:
        return "Medium"
    return "Low"


def skill_summary():
    """One row per skill: number of freelancers, averages and demand level"""
    s = df.groupby("Skill").agg(
        Freelancers=("Freelancer_ID", "count"),
        Avg_Rate=("Hourly_Rate", "mean"),
        Avg_Income=("Monthly_Income", "mean"),
        Avg_Rating=("Client_Rating", "mean"),
        Demand_Score=("Demand_Code", "mean"),
    ).reset_index()
    s["Demand"] = s["Demand_Score"].apply(demand_label)
    return s


# ---------------------------------------------------------------
# PAGES
# ---------------------------------------------------------------
@app.route("/")
def index():
    skills = skill_summary()
    top_demand = skills.sort_values(["Freelancers", "Demand_Score"], ascending=False).iloc[0]

    kpis = {
        "total": len(df),
        "avg_rate": df["Hourly_Rate"].mean(),
        "avg_income": df["Monthly_Income"].mean(),
        "top_skill": top_demand["Skill"],
    }

    # Top 5 skills by average monthly income
    top5 = skills.sort_values("Avg_Income", ascending=False).head(5).to_dict("records")

    # Key insights, all calculated from the data
    best_income = skills.sort_values("Avg_Income", ascending=False).iloc[0]
    best_rate = skills.sort_values("Avg_Rate", ascending=False).iloc[0]
    cat_income = df.groupby("Category")["Monthly_Income"].mean()
    exp_income = df.groupby("Experience_Level")["Monthly_Income"].mean()
    diff = exp_income["Expert"] - exp_income["Beginner"]
    insights = [
        ("bi-fire", "Most In-Demand Skill", f"{top_demand['Skill']} ({int(top_demand['Freelancers'])} freelancers)"),
        ("bi-trophy", "Highest-Paying Skill", f"{best_income['Skill']} ({inr(best_income['Avg_Income'])}/month)"),
        ("bi-cash-coin", "Average Monthly Income", inr(df["Monthly_Income"].mean())),
        ("bi-grid", "Highest-Paying Category", f"{cat_income.idxmax()} ({inr(cat_income.max())}/month)"),
        ("bi-graph-up-arrow", "Expert vs Beginner Income Gap",
         f"{inr(diff)} more per month ({exp_income['Expert'] / exp_income['Beginner']:.1f}x)"),
        ("bi-clock-history", "Highest Average Hourly Rate", f"{best_rate['Skill']} ({inr(best_rate['Avg_Rate'])}/hour)"),
    ]
    return render_template("index.html", kpis=kpis, top5=top5, insights=insights, metrics=model_metrics)


@app.route("/explore")
def explore():
    return render_template("explore.html",
                           skills=sorted(df["Skill"].unique()),
                           categories=sorted(df["Category"].unique()))


@app.route("/about")
def about():
    # EDA tables shown on the About page
    uni_cols = ["Hourly_Rate", "Monthly_Income", "Client_Rating"]
    desc = df[uni_cols].describe().round(2).T.reset_index()           # univariate analysis
    corr_cols = ["Experience_Code", "Hourly_Rate", "Hours_Per_Week",
                 "Projects_Completed", "Client_Rating", "Monthly_Income"]
    corr = df[corr_cols].corr().round(2)                              # correlation matrix
    coefs = [(f, round(c, 2)) for f, c in zip(FEATURES, model.coef_)]
    return render_template("about.html", prep=prep_report, desc=desc.to_dict("records"),
                           corr_cols=corr_cols, corr=corr.values.tolist(),
                           metrics=model_metrics, coefs=coefs, intercept=round(model.intercept_))


# ---------------------------------------------------------------
# JSON APIs used by JavaScript
# ---------------------------------------------------------------
@app.route("/api/chart-data")
def chart_data():
    skills = skill_summary()
    by_count = skills.sort_values("Freelancers", ascending=False)
    by_income = skills.sort_values("Avg_Income", ascending=False)
    exp = df.groupby("Experience_Level")["Monthly_Income"].mean().reindex(["Beginner", "Intermediate", "Expert"])
    return jsonify({
        "demand": {"labels": by_count["Skill"].tolist(), "values": by_count["Freelancers"].tolist()},
        "income": {"labels": by_income["Skill"].tolist(), "values": by_income["Avg_Income"].round().tolist()},
        "experience": {"labels": exp.index.tolist(), "values": exp.round().tolist()},
        "scatter": [{"x": float(r), "y": float(c)} for r, c in zip(df["Hourly_Rate"], df["Client_Rating"])],
        "correlation": round(float(df["Hourly_Rate"].corr(df["Client_Rating"])), 2),
    })


@app.route("/api/records")
def records():
    cols = ["Skill", "Category", "Experience_Level", "Hourly_Rate", "Projects_Completed",
            "Client_Rating", "Monthly_Income", "Job_Demand"]
    return jsonify(df[cols].to_dict("records"))


@app.route("/api/compare")
def compare():
    s1, s2 = request.args.get("skill1"), request.args.get("skill2")
    skills = skill_summary().set_index("Skill")
    if s1 not in skills.index or s2 not in skills.index:
        return jsonify({"error": "Please select two valid skills."}), 400
    if s1 == s2:
        return jsonify({"error": "Please select two different skills."}), 400
    a, b = skills.loc[s1], skills.loc[s2]

    # Build a simple conclusion from the numbers
    income_winner = s1 if a["Avg_Income"] > b["Avg_Income"] else s2
    demand_winner = s1 if a["Freelancers"] > b["Freelancers"] else s2
    income_loser = s2 if income_winner == s1 else s1
    if a["Freelancers"] == b["Freelancers"]:
        conclusion = f"{income_winner} has a higher average monthly income, and both skills have the same number of freelancers."
    elif income_winner == demand_winner:
        conclusion = f"{income_winner} has both a higher average monthly income and higher demand than {income_loser}."
    else:
        conclusion = (f"{income_winner} has a higher average monthly income, "
                      f"while {demand_winner} has higher demand.")

    def row(metric, va, vb):
        return {"metric": metric, "a": va, "b": vb}
    rows = [
        row("Demand", f"{a['Demand']} ({int(a['Freelancers'])} freelancers)", f"{b['Demand']} ({int(b['Freelancers'])} freelancers)"),
        row("Avg Hourly Rate", inr(a["Avg_Rate"]), inr(b["Avg_Rate"])),
        row("Avg Monthly Income", inr(a["Avg_Income"]), inr(b["Avg_Income"])),
        row("Avg Rating", f"{a['Avg_Rating']:.2f}", f"{b['Avg_Rating']:.2f}"),
    ]
    return jsonify({"skill1": s1, "skill2": s2, "rows": rows, "conclusion": conclusion})


@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    try:
        experience = data["experience"]
        if experience not in EXPERIENCE_MAP:
            raise ValueError("Choose an experience level.")
        values = {
            "Experience_Code": EXPERIENCE_MAP[experience],
            "Hourly_Rate": float(data["hourly_rate"]),
            "Hours_Per_Week": float(data["hours_per_week"]),
            "Projects_Completed": float(data["projects"]),
            "Client_Rating": float(data["rating"]),
        }
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Please fill in all fields with valid numbers."}), 400

    if not (1 <= values["Hours_Per_Week"] <= 80 and 1 <= values["Client_Rating"] <= 5 and values["Hourly_Rate"] > 0):
        return jsonify({"error": "Check the ranges: hours 1-80, rating 1-5, hourly rate above 0."}), 400

    X_new = pd.DataFrame([values])[FEATURES]
    estimate = max(0, float(model.predict(X_new)[0]))      # income cannot be negative
    return jsonify({"estimate": round(estimate), "formatted": inr(estimate)})


if __name__ == "__main__":
    app.run(debug=True)
