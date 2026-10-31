🔗 **Live Dashboard:** https://freelancing-analytics-1.onrender.com


# Freelancing Income & Skill Demand Analytics

## 1. Project Name
Freelancing Income & Skill Demand Analytics (College project: Computational Data Analytics)

## 2. Introduction
A small web dashboard that analyzes freelancing data to show which skills are in demand and which skills have better earning potential.

## 3. Problem Statement
Freelancing has become an important source of income, but beginners often do not know which skills are in demand or which skills provide better earning opportunities.

## 4. Objectives
- Find the most in-demand skills
- Compare average hourly rate and monthly income across skills and categories
- Check whether experience affects income
- Predict approximate monthly income with a simple Linear Regression model

## 5. Features
- Dashboard with 4 KPI cards and 4 charts (Chart.js)
- Top 5 skills by earning potential and automatic Key Insights
- Skill Explorer: search box, 4 filters (skill, category, experience, demand)
- Compare any two skills with an automatic conclusion
- Income Predictor (Linear Regression)
- About page with preprocessing report, EDA tables and correlation table

## 6. Technologies
Python, Flask, Pandas, NumPy, Scikit-learn, HTML, CSS, Bootstrap 5, JavaScript, Chart.js (Bootstrap and Chart.js load from a CDN, so an internet connection is needed for styling and charts).

## 7. Dataset
`data/freelancing_data.csv` has 150 records and 11 columns: Freelancer_ID, Skill, Category, Experience_Level, Location, Projects_Completed, Hourly_Rate, Hours_Per_Week, Client_Rating, Monthly_Income, Job_Demand. It is a sample dataset created for this project (not real platform data). Income is in Indian Rupees.

## 8. Machine Learning Model
- Model: Linear Regression (scikit-learn)
- Target: Monthly_Income
- Features: Experience_Level (Beginner=0, Intermediate=1, Expert=2), Hourly_Rate, Hours_Per_Week, Projects_Completed, Client_Rating
- Split: 80% training, 20% testing (random_state=42)
- Metrics: R² Score and Mean Absolute Error (shown on the website)

## 9. How to Install
```bash
pip install -r requirements.txt
```

## 10. How to Run
```bash
python app.py
```
Open http://127.0.0.1:5000 in your browser.

## 11. Future Scope
- Use a larger real-world dataset
- Add more features such as country or platform
- Try other models and compare them
- Add downloadable reports
