from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

st.set_page_config(
    page_title="Canadian Grocery Affordability Dashboard",
    page_icon="🛒",
    layout="wide",
)


@st.cache_data
def load_csv(path):
    df = pd.read_csv(path, low_memory=False)

    if "period" in df.columns:
        df["period"] = pd.to_datetime(df["period"], errors="coerce")

    return df


def safe_load(path):
    if not path.exists():
        return pd.DataFrame()

    return load_csv(path)


retail_prices = safe_load(PROCESSED_DIR / "retail_prices_clean.csv")
cpi_pressure = safe_load(OUTPUT_DIR / "grocery_affordability_pressure.csv")
top_rising = safe_load(OUTPUT_DIR / "top_rising_products.csv")
top_falling = safe_load(OUTPUT_DIR / "top_falling_products.csv")
category_summary = safe_load(OUTPUT_DIR / "category_price_summary.csv")
retail_volume = safe_load(OUTPUT_DIR / "latest_retail_price_volume_trends.csv")
food_insecurity = safe_load(OUTPUT_DIR / "latest_food_insecurity.csv")
project_summary = safe_load(OUTPUT_DIR / "project_summary.csv")

st.title("Canadian Grocery Affordability Dashboard")

st.write(
    "This dashboard tracks grocery prices, CPI pressure, food insecurity, "
    "and real retail activity using Statistics Canada datasets."
)

if retail_prices.empty:
    st.error("No processed data found. Run `python run_pipeline.py` first.")
    st.stop()


if not project_summary.empty:
    row = project_summary.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Products tracked", int(row["products_tracked"]))
    col2.metric("Latest price month", row["latest_price_month"])
    col3.metric(
        "Avg latest price growth",
        f"{row['average_latest_product_price_growth_percent']}%",
    )
    col4.metric(
        "Highest food insecurity",
        f"{row['highest_food_insecurity_percent']}%",
    )


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Price tracker",
        "Top changes",
        "CPI pressure",
        "Retail volume",
        "Food insecurity",
    ]
)


with tab1:
    st.subheader("Grocery price tracker")

    geographies = sorted(retail_prices["geo"].dropna().unique())

    selected_geo = st.selectbox(
        "Geography",
        geographies,
        index=geographies.index("Canada") if "Canada" in geographies else 0,
    )

    available_products = sorted(
        retail_prices.loc[
            retail_prices["geo"].eq(selected_geo),
            "product",
        ]
        .dropna()
        .unique()
    )

    default_products = available_products[:5]

    selected_products = st.multiselect(
        "Products",
        available_products,
        default=default_products,
    )

    chart_data = retail_prices[
        retail_prices["geo"].eq(selected_geo)
        & retail_prices["product"].isin(selected_products)
    ].copy()

    if chart_data.empty:
        st.info("Select at least one product.")
    else:
        fig = px.line(
            chart_data,
            x="period",
            y="price",
            color="product",
            title=f"Monthly grocery prices in {selected_geo}",
            labels={
                "period": "Month",
                "price": "Average retail price",
                "product": "Product",
            },
        )

        st.plotly_chart(fig, use_container_width=True)

        latest = (
            chart_data.sort_values("period")
            .groupby("product", as_index=False)
            .tail(1)
            .sort_values("price_yoy_change_percent", ascending=False)
        )

        st.dataframe(latest, use_container_width=True)


with tab2:
    st.subheader("Fastest rising and falling grocery products")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Fastest rising products")

        if top_rising.empty:
            st.info("Run `python src/analysis.py` first.")
        else:
            fig = px.bar(
                top_rising.sort_values("price_yoy_change_percent"),
                x="price_yoy_change_percent",
                y="product",
                orientation="h",
                title="Highest latest year-over-year price growth",
                labels={
                    "price_yoy_change_percent": "YoY price growth (%)",
                    "product": "Product",
                },
            )

            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(top_rising, use_container_width=True)

    with col2:
        st.write("Fastest falling products")

        if top_falling.empty:
            st.info("Run `python src/analysis.py` first.")
        else:
            fig = px.bar(
                top_falling.sort_values("price_yoy_change_percent"),
                x="price_yoy_change_percent",
                y="product",
                orientation="h",
                title="Lowest latest year-over-year price growth",
                labels={
                    "price_yoy_change_percent": "YoY price growth (%)",
                    "product": "Product",
                },
            )

            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(top_falling, use_container_width=True)

    st.subheader("Price growth by grocery group")

    if not category_summary.empty:
        fig = px.bar(
            category_summary,
            x="product_group",
            y="average_yoy_growth",
            title="Average latest price growth by grocery group",
            labels={
                "product_group": "Grocery group",
                "average_yoy_growth": "Average YoY growth (%)",
            },
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(category_summary, use_container_width=True)


with tab3:
    st.subheader("Food CPI compared with overall CPI")

    if cpi_pressure.empty:
        st.info("Run `python src/analysis.py` first.")
    else:
        fig = px.line(
            cpi_pressure,
            x="period",
            y="food_minus_overall_cpi_growth",
            color="geo",
            title="Food CPI growth minus overall CPI growth",
            labels={
                "period": "Month",
                "food_minus_overall_cpi_growth": "Difference in YoY growth points",
                "geo": "Geography",
            },
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(cpi_pressure.tail(24), use_container_width=True)


with tab4:
    st.subheader("Real retail activity for grocery-related industries")

    if retail_volume.empty:
        st.info("Run `python src/analysis.py` first.")
    else:
        fig = px.bar(
            retail_volume,
            x="industry",
            y="measure_yoy_change_percent",
            title="Latest real retail sales growth",
            labels={
                "industry": "Industry",
                "measure_yoy_change_percent": "YoY change (%)",
            },
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(retail_volume, use_container_width=True)


with tab5:
    st.subheader("Food insecurity")

    if food_insecurity.empty:
        st.info("Run `python src/analysis.py` first.")
    else:
        selected_status = st.selectbox(
            "Food security status",
            sorted(food_insecurity["food_security_status"].dropna().unique()),
        )

        filtered = food_insecurity[
            food_insecurity["food_security_status"].eq(selected_status)
        ].copy()

        fig = px.bar(
            filtered.head(15).sort_values("food_insecurity_percent"),
            x="food_insecurity_percent",
            y="demographic",
            orientation="h",
            title=f"Latest food insecurity by demographic: {selected_status}",
            labels={
                "food_insecurity_percent": "Percent of persons",
                "demographic": "Demographic group",
            },
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(filtered, use_container_width=True)

    st.markdown(
        """
        ### Interpretation notes

        A useful policy reading is:

        - If grocery prices rise faster than overall CPI, food affordability pressure is increasing.
        - If real grocery-related retail volume falls while prices rise, households may be buying less even while spending more.
        - If food insecurity remains high for specific groups, targeted support may be more useful than broad messaging.
        """
    )