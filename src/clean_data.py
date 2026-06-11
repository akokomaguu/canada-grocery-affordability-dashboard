from pathlib import Path
import csv
import re
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def find_raw_file(table_id: str) -> Path:
    matches = sorted(RAW_DIR.glob(f"*{table_id}*.csv"))

    if not matches:
        raise FileNotFoundError(
            f"No CSV file containing '{table_id}' was found in {RAW_DIR}"
        )

    return matches[0]


def read_csv_rows(table_id: str) -> list[list[str]]:
    path = find_raw_file(table_id)

    print(f"Reading {path.name}")

    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as file:
        return list(csv.reader(file))


def text_clean(value) -> str:
    if value is None:
        return ""

    value = str(value).replace("\xa0", " ").strip()
    value = re.sub(r"\s+", " ", value)

    return value


def clean_label(label: str) -> str:
    label = text_clean(label)
    label = re.sub(r"\s+\d+$", "", label)
    return label.strip()


def clean_number(value):
    value = text_clean(value)

    if value in {"", "..", "...", "x", "X", "F", "N/A"}:
        return pd.NA

    value = value.replace(",", "")
    value = re.sub(r"[A-Za-z*]+$", "", value)
    value = re.sub(r"[^0-9.\-]", "", value)

    if value in {"", "-", "."}:
        return pd.NA

    try:
        return float(value)
    except ValueError:
        return pd.NA


def parse_month_label(value):
    value = text_clean(value)

    if not value:
        return pd.NaT

    return pd.to_datetime(value, format="%B %Y", errors="coerce")


def first_filled_after_first_cell(row):
    for value in row[1:]:
        value = text_clean(value)

        if value:
            return value

    return ""


def find_row_index(rows, labels):
    for index, row in enumerate(rows):
        first_cell = text_clean(row[0]) if row else ""

        for label in labels:
            label = text_clean(label)

            if label.endswith("*"):
                if first_cell.startswith(label[:-1]):
                    return index
            elif first_cell == label:
                return index

    raise ValueError(f"Could not find row matching: {labels}")


def get_metadata(rows, label):
    for row in rows:
        if row and text_clean(row[0]) == label:
            return first_filled_after_first_cell(row)

    return ""


def melt_monthly_table(
    rows,
    header_label,
    entity_column,
    value_column,
    geo_from_metadata=True,
    extra_fields=None,
):
    header_index = find_row_index(rows, [header_label])
    header = [text_clean(value) for value in rows[header_index]]
    uom = first_filled_after_first_cell(rows[header_index + 1])
    geography = get_metadata(rows, "Geography") if geo_from_metadata else ""

    records = []

    for row in rows[header_index + 2:]:
        if not row:
            continue

        entity = clean_label(row[0])

        if not entity:
            continue

        lowered = entity.lower()

        if lowered.startswith(("source", "footnotes", "notes", "note", "how to cite")):
            break

        if re.fullmatch(r"\d+", entity):
            break

        for col_index in range(1, len(header)):
            if col_index >= len(row):
                continue

            period = parse_month_label(header[col_index])

            if pd.isna(period):
                continue

            number = clean_number(row[col_index])

            if pd.isna(number):
                continue

            record = {
                entity_column: entity,
                "period": period,
                "year": period.year,
                "month": period.month,
                "uom": uom,
                value_column: number,
            }

            if geo_from_metadata:
                record["geo"] = geography
            else:
                record["geo"] = entity

            if extra_fields:
                record.update(extra_fields)

            records.append(record)

    return pd.DataFrame(records)


def add_yoy_change(df, group_columns, value_column, output_column):
    df = df.copy()
    df = df.sort_values(group_columns + ["period"])

    df[output_column] = (
        df.groupby(group_columns)[value_column]
        .pct_change(12)
        .mul(100)
    )

    return df


def clean_retail_prices():
    rows = read_csv_rows("18100245")

    df = melt_monthly_table(
        rows=rows,
        header_label="Products",
        entity_column="product",
        value_column="price",
        geo_from_metadata=True,
    )

    df = add_yoy_change(
        df,
        group_columns=["geo", "product"],
        value_column="price",
        output_column="price_yoy_change_percent",
    )

    output_path = PROCESSED_DIR / "retail_prices_clean.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved {output_path.name}: {len(df):,} rows")

    return df


def clean_cpi():
    rows = read_csv_rows("18100004")

    df = melt_monthly_table(
        rows=rows,
        header_label="Products and product groups*",
        entity_column="cpi_category",
        value_column="cpi_value",
        geo_from_metadata=True,
    )

    useful_terms = (
        "all-items|all items|food|meat|dairy|bakery|fruit|vegetable|"
        "eggs|fish|chicken|beef|pork|bread|cereal|milk"
    )

    df = df[
        df["cpi_category"].str.lower().str.contains(useful_terms, na=False)
    ].copy()

    df = add_yoy_change(
        df,
        group_columns=["geo", "cpi_category"],
        value_column="cpi_value",
        output_column="cpi_yoy_change_percent",
    )

    output_path = PROCESSED_DIR / "cpi_clean.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved {output_path.name}: {len(df):,} rows")

    return df


def clean_retail_trade_sales():
    rows = read_csv_rows("20100056")

    industry = get_metadata(rows, "North American Industry Classification System (NAICS)")
    sales_type = get_metadata(rows, "Sales")
    adjustment = get_metadata(rows, "Adjustments")

    df = melt_monthly_table(
        rows=rows,
        header_label="Geography",
        entity_column="geo",
        value_column="retail_sales",
        geo_from_metadata=False,
        extra_fields={
            "industry": clean_label(industry),
            "sales_type": clean_label(sales_type),
            "adjustment": clean_label(adjustment),
        },
    )

    df = add_yoy_change(
        df,
        group_columns=["geo", "industry"],
        value_column="retail_sales",
        output_column="retail_sales_yoy_change_percent",
    )

    output_path = PROCESSED_DIR / "retail_trade_sales_clean.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved {output_path.name}: {len(df):,} rows")

    return df


def clean_retail_price_volume():
    rows = read_csv_rows("20100067")

    measure = get_metadata(rows, "Sales, price and volume")

    df = melt_monthly_table(
        rows=rows,
        header_label="North American Industry Classification System (NAICS)",
        entity_column="industry",
        value_column="measure_value",
        geo_from_metadata=True,
        extra_fields={
            "measure": clean_label(measure),
        },
    )

    grocery_terms = "food|beverage|grocery|supermarket|convenience|specialty food"

    df = df[
        df["industry"].str.lower().str.contains(grocery_terms, na=False)
    ].copy()

    df = add_yoy_change(
        df,
        group_columns=["geo", "industry", "measure"],
        value_column="measure_value",
        output_column="measure_yoy_change_percent",
    )

    output_path = PROCESSED_DIR / "retail_price_volume_clean.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved {output_path.name}: {len(df):,} rows")

    return df


def clean_food_insecurity():
    rows = read_csv_rows("13100835")

    geography = get_metadata(rows, "Geography")

    status_index = find_row_index(rows, ["Household food security status"])
    statistics_index = find_row_index(rows, ["Statistics"])
    year_index = find_row_index(rows, ["Demographic characteristics"])

    status_row = rows[status_index]
    statistics_row = rows[statistics_index]
    year_row = rows[year_index]

    records = []
    active_status = ""
    active_statistic = ""

    for col_index in range(1, len(year_row)):
        if col_index < len(status_row) and text_clean(status_row[col_index]):
            active_status = clean_label(status_row[col_index])

        if col_index < len(statistics_row) and text_clean(statistics_row[col_index]):
            active_statistic = clean_label(statistics_row[col_index])

        year = pd.to_numeric(text_clean(year_row[col_index]), errors="coerce")

        if pd.isna(year):
            continue

        for row in rows[year_index + 2:]:
            if not row:
                continue

            demographic = clean_label(row[0])

            if not demographic:
                continue

            lowered = demographic.lower()

            if lowered.startswith(("source", "footnotes", "notes", "note", "how to cite")):
                break

            if re.fullmatch(r"\d+", demographic):
                break

            value = clean_number(row[col_index] if col_index < len(row) else "")

            if pd.isna(value):
                continue

            records.append(
                {
                    "geo": geography,
                    "year": int(year),
                    "demographic": demographic,
                    "food_security_status": active_status,
                    "statistic": active_statistic,
                    "food_insecurity_percent": value,
                }
            )

    df = pd.DataFrame(records)

    df = df.sort_values(
        ["geo", "demographic", "food_security_status", "year"]
    )

    df["food_insecurity_yoy_change_points"] = (
        df.groupby(["geo", "demographic", "food_security_status"])["food_insecurity_percent"]
        .diff()
    )

    output_path = PROCESSED_DIR / "food_insecurity_clean.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved {output_path.name}: {len(df):,} rows")

    return df


def run_cleaning_pipeline():
    clean_retail_prices()
    clean_cpi()
    clean_retail_trade_sales()
    clean_retail_price_volume()
    clean_food_insecurity()

    print("\nCleaning finished. Processed files are in data/processed/.")


if __name__ == "__main__":
    run_cleaning_pipeline()