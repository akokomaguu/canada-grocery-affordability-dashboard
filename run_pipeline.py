from src.clean_data import run_cleaning_pipeline
from src.analysis import run_analysis_pipeline


def main():
    print("STEP 1: Cleaning raw CSV files")
    run_cleaning_pipeline()

    print("\nSTEP 2: Running analysis")
    run_analysis_pipeline()

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()