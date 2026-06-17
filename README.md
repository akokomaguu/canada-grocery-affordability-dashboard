# Canadian Grocery Affordability Dashboard

An interactive data analytics project that examines grocery affordability in Canada using official Statistics Canada datasets. The project analyses retail food prices, consumer price inflation, retail sales, food insecurity, and province-level grocery price pressure.

The goal is to show how data science can support public policy, retail strategy, and consumer affordability monitoring.

## Project Overview

Grocery affordability has become an important policy and household concern in Canada. This project uses open Canadian data to answer questions such as:

* Which grocery products are increasing fastest in price?
* Which provinces experience the highest grocery price pressure?
* Are food prices rising faster than overall inflation?
* How do retail sales trends relate to food affordability?
* What policy issues should be monitored using the data?

## Data Sources

This project uses the following Statistics Canada datasets:

1. **Table 18-10-0245-01**
   Monthly average retail prices for selected products.

2. **Table 18-10-0004-01**
   Consumer Price Index, monthly.

3. **Table 20-10-0056-01**
   Monthly retail trade sales by province and territory.

4. **Table 20-10-0067-01**
   Retail sales, price and volume.

5. **Table 13-10-0835-01**
   Food insecurity by selected demographic characteristics.

## Tools and Technologies

* Python
* pandas
* Streamlit
* Plotly
* Matplotlib
* Statistics Canada open data
* Data cleaning
* Exploratory data analysis
* Policy analytics
* Dashboard development

## Project Structure

```text
canada-grocery-affordability-dashboard/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── images/
├── notebooks/
│   ├── 01_data_understanding.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_affordability_analysis.ipynb
│   └── 04_forecasting_model.ipynb
│
├── outputs/
├── reports/
├── src/
│   ├── analysis.py
│   ├── clean_data.py
│   └── dashboard.py
│
├── README.md
├── requirements.txt
└── .gitignore
```

## Main Features

### 1. Grocery Price Tracker

Tracks monthly retail prices for selected grocery products across Canada and provinces.

### 2. Province Price Pressure

Compares average year-over-year grocery price growth across Canadian provinces and territories.

### 3. CPI Affordability Analysis

Compares food inflation with overall inflation using a grocery affordability pressure metric:

```text
Grocery Affordability Pressure = Food CPI YoY Change - Overall CPI YoY Change
```

A positive value suggests food prices are rising faster than general consumer prices.

### 4. Retail Sales Analysis

Analyses retail sales growth patterns related to food, beverage, grocery, supermarket, and retail sectors.

### 5. Policy Interpretation

Connects data findings to practical policy issues such as grocery competition, unit pricing, food basket monitoring, and household affordability support.

## How to Run the Project Locally

Clone the repository:

```bash
git clone https://github.com/akokomaguu/canada-grocery-affordability-dashboard.git
```

Move into the project folder:

```bash
cd canada-grocery-affordability-dashboard
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the data cleaning script:

```bash
python src/clean_data.py
```

Run the analysis script:

```bash
python src/analysis.py
```

Launch the dashboard:

```bash
streamlit run src/dashboard.py
```

## Key Outputs

The project generates cleaned datasets and analysis outputs in:

```text
data/processed/
outputs/
```

These files are used by the Streamlit dashboard.

## Dashboard Preview

Add dashboard screenshots here after deployment.

```text
images/
```

Recommended screenshots:

* Price tracker
* Province price pressure
* CPI affordability pressure
* Retail sales analysis
* Policy notes page

## Policy Relevance

This project demonstrates how public datasets can be used to monitor grocery affordability and support evidence-based decisions. The dashboard can help identify food categories and regions experiencing higher affordability pressure, which may be useful for policy analysts, retail analysts, researchers, and consumer-focused organizations.

## Author

**Malon Aoko**
Data Scientist | Data Analyst | Statistician
Python • R • Excel • Dashboards • Statistical Modelling • GIS • Machine Learning

GitHub: [akokomaguu](https://github.com/akokomaguu)
LinkedIn: https://www.linkedin.com/in/malon-aoko-9a1377334/

## Project Status

This project is currently in development. Future improvements may include:

* Adding wage data to improve the affordability index.
* Adding forecasting models for selected grocery products.
* Creating a downloadable policy brief.
* Expanding visualizations by province and product category.
* Deploying the dashboard using Streamlit Community Cloud.
