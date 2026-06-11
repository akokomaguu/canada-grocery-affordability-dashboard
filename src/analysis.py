from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_processed_file(filename):
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run src/clean_data.py first.")

    df = pd.read_csv(path, low_memory=False)

    if "period" in df.columns:
        df["period"] = pd.to_datetime(df["period"], errors="coerce")

    return df


def latest_available_rows(df, group_columns, date_column="period"):
    return (
        df.dropna(subset=[date_column])
        .sort_values(date_column)
        .groupby(group_columns, as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )


def top_rising_products(geo="Canada", top_n=15):
    prices = load_processed_file("retail_prices_clean.csv")
    prices = prices[prices["geo"].eq(geo)].copy()

    latest = latest_available_rows(prices, ["geo", "product"])
    latest = latest.dropna(subset=["price_yoy_change_percent"])

    result = (
        latest.sort_values("price_yoy_change_percent", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    result.to_csv(OUTPUT_DIR / "top_rising_products.csv", index=False)

    print(f"Saved top_rising_products.csv: {len(result):,} rows")

    return result


def top_falling_products(geo="Canada", top_n=15):
    prices = load_processed_file("retail_prices_clean.csv")
    prices = prices[prices["geo"].eq(geo)].copy()

    latest = latest_available_rows(prices, ["geo", "product"])
    latest = latest.dropna(subset=["price_yoy_change_percent"])

    result = (
        latest.sort_values("price_yoy_change_percent", ascending=True)
        .head(top_n)
        .reset_index(drop=True)
    )

    result.to_csv(OUTPUT_DIR / "top_falling_products.csv", index=False)

    print(f"Saved top_falling_products.csv: {len(result):,} rows")

    return result


def category_price_summary(geo="Canada"):
    prices = load_processed_file("retail_prices_clean.csv")
    prices = prices[prices["geo"].eq(geo)].copy()

    latest = latest_available_rows(prices, ["geo", "product"])
    latest = latest.dropna(subset=["price_yoy_change_percent"])

    def product_group(product):
        product = str(product).lower()

        if any(term in product for term in ["beef", "pork", "chicken", "bacon", "wiener", "salmon", "tuna", "shrimp"]):
            return "Meat and seafood"

        if any(term in product for term in ["milk", "cheese", "cream", "butter", "yogurt", "eggs"]):
            return "Dairy and eggs"

        if any(term in product for term in ["apple", "banana", "orange", "berries", "grapes", "fruit"]):
            return "Fruit"

        if any(term in product for term in ["potato", "tomato", "lettuce", "onion", "carrot", "cabbage", "vegetable"]):
            return "Vegetables"

        if any(term in product for term in ["bread", "rice", "pasta", "flour", "cereal", "oat"]):
            return "Grains and bakery"

        return "Other grocery items"

    latest["product_group"] = latest["product"].apply(product_group)

    result = (
        latest.groupby("product_group", as_index=False)
        .agg(
            products=("product", "nunique"),
            average_latest_price=("price", "mean"),
            average_yoy_growth=("price_yoy_change_percent", "mean"),
            median_yoy_growth=("price_yoy_change_percent", "median"),
            highest_growth=("price_yoy_change_percent", "max"),
        )
        .sort_values("average_yoy_growth", ascending=False)
        .reset_index(drop=True)
    )

    result.to_csv(OUTPUT_DIR / "category_price_summary.csv", index=False)

    print(f"Saved category_price_summary.csv: {len(result):,} rows")

    return result


def grocery_affordability_pressure():
    cpi = load_processed_file("cpi_clean.csv")
    cpi["category_lower"] = cpi["cpi_category"].str.lower()

    all_items = cpi[cpi["category_lower"].isin(["all-items", "all items"])].copy()
    food = cpi[cpi["category_lower"].eq("food")].copy()

    if food.empty:
        food = cpi[cpi["category_lower"].str.contains("food", na=False)].copy()

    all_items = all_items.rename(
        columns={
            "cpi_value": "overall_cpi",
            "cpi_yoy_change_percent": "overall_cpi_yoy_change_percent",
        }
    )

    food = food.rename(
        columns={
            "cpi_value": "food_cpi",
            "cpi_yoy_change_percent": "food_cpi_yoy_change_percent",
        }
    )

    result = food.merge(
        all_items[["geo", "period", "overall_cpi", "overall_cpi_yoy_change_percent"]],
        on=["geo", "period"],
        how="left",
    )

    result["food_minus_overall_cpi_growth"] = (
        result["food_cpi_yoy_change_percent"]
        - result["overall_cpi_yoy_change_percent"]
    )

    result.to_csv(OUTPUT_DIR / "grocery_affordability_pressure.csv", index=False)

    print(f"Saved grocery_affordability_pressure.csv: {len(result):,} rows")

    return result


def retail_trade_latest():
    sales = load_processed_file("retail_trade_sales_clean.csv")

    latest = latest_available_rows(sales, ["geo", "industry"])
    latest = latest.sort_values("retail_sales", ascending=False).reset_index(drop=True)

    latest.to_csv(OUTPUT_DIR / "latest_retail_trade_sales.csv", index=False)

    print(f"Saved latest_retail_trade_sales.csv: {len(latest):,} rows")

    return latest


def retail_price_volume_trends():
    volume = load_processed_file("retail_price_volume_clean.csv")

    latest = latest_available_rows(volume, ["geo", "industry", "measure"])
    latest = latest.sort_values("measure_yoy_change_percent", ascending=False)

    latest.to_csv(OUTPUT_DIR / "latest_retail_price_volume_trends.csv", index=False)

    print(f"Saved latest_retail_price_volume_trends.csv: {len(latest):,} rows")

    return latest


def food_insecurity_latest():
    food = load_processed_file("food_insecurity_clean.csv")

    result = (
        food.sort_values("year")
        .groupby(["geo", "demographic", "food_security_status"], as_index=False)
        .tail(1)
        .sort_values("food_insecurity_percent", ascending=False)
        .reset_index(drop=True)
    )

    result.to_csv(OUTPUT_DIR / "latest_food_insecurity.csv", index=False)

    print(f"Saved latest_food_insecurity.csv: {len(result):,} rows")

    return result


def build_project_summary():
    prices = load_processed_file("retail_prices_clean.csv")
    cpi = load_processed_file("cpi_clean.csv")
    insecurity = load_processed_file("food_insecurity_clean.csv")

    latest_products = latest_available_rows(prices, ["geo", "product"])
    latest_products = latest_products.dropna(subset=["price_yoy_change_percent"])

    latest_food_cpi = grocery_affordability_pressure()
    latest_food_cpi = latest_food_cpi.dropna(subset=["food_minus_overall_cpi_growth"])

    latest_insecurity = food_insecurity_latest()

    summary = {
        "latest_price_month": str(prices["period"].max().date()),
        "products_tracked": int(prices["product"].nunique()),
        "average_latest_product_price_growth_percent": round(
            latest_products["price_yoy_change_percent"].mean(), 2
        ),
        "latest_cpi_month": str(cpi["period"].max().date()),
        "latest_food_minus_overall_cpi_growth_points": round(
            latest_food_cpi.sort_values("period")
            .tail(1)["food_minus_overall_cpi_growth"]
            .iloc[0],
            2,
        ),
        "latest_food_insecurity_year": int(insecurity["year"].max()),
        "highest_food_insecurity_group": latest_insecurity.iloc[0]["demographic"],
        "highest_food_insecurity_percent": latest_insecurity.iloc[0]["food_insecurity_percent"],
    }

    result = pd.DataFrame([summary])
    result.to_csv(OUTPUT_DIR / "project_summary.csv", index=False)

    print("Saved project_summary.csv: 1 row")

    return result


def run_analysis_pipeline():
    top_rising_products()
    top_falling_products()
    category_price_summary()
    grocery_affordability_pressure()
    retail_trade_latest()
    retail_price_volume_trends()
    food_insecurity_latest()
    build_project_summary()

    print("\nAnalysis finished. Output files are in outputs/.")


if __name__ == "__main__":
    run_analysis_pipeline()