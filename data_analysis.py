"""Task 1: Dataset Analysis and Insights.

Run from a terminal with:
    python3 data_analysis.py

By default, the script looks for All_Diets.csv beside this file or inside
an archive/ folder. All tables and charts are written to outputs/.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Save charts without requiring a graphical display.

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


REQUIRED_COLUMNS = [
    "Diet_type",
    "Recipe_name",
    "Cuisine_type",
    "Protein(g)",
    "Carbs(g)",
    "Fat(g)",
]
MACRO_COLUMNS = ["Protein(g)", "Carbs(g)", "Fat(g)"]


def find_default_dataset() -> Path:
    """Find All_Diets.csv in the two layouts used by this project."""
    script_directory = Path(__file__).resolve().parent
    candidates = [
        script_directory / "All_Diets.csv",
        script_directory / "archive" / "All_Diets.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def load_and_clean_data(csv_path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    """Load the dataset, validate its columns, and clean required fields."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {csv_path}\n"
            "Place All_Diets.csv beside data_analysis.py or in archive/."
        )

    dataframe = pd.read_csv(csv_path)
    dataframe.columns = dataframe.columns.str.strip()

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    # Normalize category values so capitalization and extra spaces do not create
    # separate diet or cuisine groups.
    for column in ["Diet_type", "Recipe_name", "Cuisine_type"]:
        dataframe[column] = dataframe[column].astype("string").str.strip()

    dataframe["Diet_type"] = dataframe["Diet_type"].str.lower()
    dataframe["Cuisine_type"] = dataframe["Cuisine_type"].str.lower()

    missing_before: dict[str, int] = {}
    for column in MACRO_COLUMNS:
        # Invalid numeric text becomes NaN and is handled like any other missing value.
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
        missing_before[column] = int(dataframe[column].isna().sum())

        mean_value = dataframe[column].mean()
        if pd.isna(mean_value):
            raise ValueError(f"Column {column} does not contain usable numeric data.")
        dataframe[column] = dataframe[column].fillna(mean_value)

    dataframe["Diet_type"] = dataframe["Diet_type"].fillna("unknown")
    dataframe["Cuisine_type"] = dataframe["Cuisine_type"].fillna("unknown")
    dataframe["Recipe_name"] = dataframe["Recipe_name"].fillna("unnamed recipe")

    # Safe division: an undefined ratio is stored as NaN rather than infinity.
    dataframe["Protein_to_Carbs_ratio"] = np.where(
        dataframe["Carbs(g)"].ne(0),
        dataframe["Protein(g)"] / dataframe["Carbs(g)"],
        np.nan,
    )
    dataframe["Carbs_to_Fat_ratio"] = np.where(
        dataframe["Fat(g)"].ne(0),
        dataframe["Carbs(g)"] / dataframe["Fat(g)"],
        np.nan,
    )

    return dataframe, missing_before


def calculate_results(dataframe: pd.DataFrame) -> dict[str, object]:
    """Calculate every statistic required by Task 1."""
    average_macros = (
        dataframe.groupby("Diet_type", as_index=False)[MACRO_COLUMNS]
        .mean()
        .sort_values("Diet_type")
    )

    top_five_protein = (
        dataframe.sort_values("Protein(g)", ascending=False)
        .groupby("Diet_type", group_keys=False)
        .head(5)[
            [
                "Diet_type",
                "Recipe_name",
                "Cuisine_type",
                "Protein(g)",
                "Carbs(g)",
                "Fat(g)",
            ]
        ]
        .sort_values(["Diet_type", "Protein(g)"], ascending=[True, False])
        .reset_index(drop=True)
    )

    highest_average_row = average_macros.loc[
        average_macros["Protein(g)"].idxmax()
    ]
    highest_recipe_row = dataframe.loc[dataframe["Protein(g)"].idxmax()]

    most_common_cuisines = (
        dataframe.groupby("Diet_type")["Cuisine_type"]
        .agg(lambda values: values.mode().iloc[0] if not values.mode().empty else "N/A")
        .rename("Most_common_cuisine")
        .reset_index()
        .sort_values("Diet_type")
    )

    return {
        "average_macros": average_macros,
        "top_five_protein": top_five_protein,
        "highest_average_diet": str(highest_average_row["Diet_type"]),
        "highest_average_protein": float(highest_average_row["Protein(g)"]),
        "highest_recipe_name": str(highest_recipe_row["Recipe_name"]),
        "highest_recipe_diet": str(highest_recipe_row["Diet_type"]),
        "highest_recipe_protein": float(highest_recipe_row["Protein(g)"]),
        "most_common_cuisines": most_common_cuisines,
    }


def save_tables(
    dataframe: pd.DataFrame, results: dict[str, object], output_directory: Path
) -> None:
    """Save the cleaned dataset and calculation tables as CSV files."""
    dataframe.to_csv(output_directory / "processed_diets.csv", index=False)
    results["average_macros"].to_csv(
        output_directory / "average_macronutrients.csv", index=False
    )
    results["top_five_protein"].to_csv(
        output_directory / "top_5_protein_recipes.csv", index=False
    )
    results["most_common_cuisines"].to_csv(
        output_directory / "most_common_cuisines.csv", index=False
    )


def save_visualizations(
    results: dict[str, object], output_directory: Path, run_time: datetime
) -> None:
    """Create the three visualization types required by Task 1."""
    sns.set_theme(style="whitegrid")
    timestamp = run_time.strftime("%Y-%m-%d %H:%M:%S")

    average_macros = results["average_macros"]
    chart_data = average_macros.melt(
        id_vars="Diet_type",
        value_vars=MACRO_COLUMNS,
        var_name="Macronutrient",
        value_name="Average grams",
    )

    plt.figure(figsize=(12, 7))
    sns.barplot(
        data=chart_data,
        x="Diet_type",
        y="Average grams",
        hue="Macronutrient",
        palette="Set2",
    )
    plt.title(f"Average Macronutrients by Diet Type\nGenerated {timestamp}")
    plt.xlabel("Diet Type")
    plt.ylabel("Average Macronutrient Content (g)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(output_directory / "bar_chart_average_macronutrients.png", dpi=300)
    plt.close()

    heatmap_data = average_macros.set_index("Diet_type")[MACRO_COLUMNS]
    plt.figure(figsize=(9, 6))
    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        linewidths=0.5,
        cbar_kws={"label": "Average grams"},
    )
    plt.title(f"Macronutrient Heatmap by Diet Type\nGenerated {timestamp}")
    plt.xlabel("Macronutrient")
    plt.ylabel("Diet Type")
    plt.tight_layout()
    plt.savefig(output_directory / "heatmap_macronutrients.png", dpi=300)
    plt.close()

    top_five = results["top_five_protein"]
    plt.figure(figsize=(14, 8))
    sns.scatterplot(
        data=top_five,
        x="Cuisine_type",
        y="Protein(g)",
        hue="Diet_type",
        style="Diet_type",
        s=130,
        alpha=0.85,
        palette="tab10",
    )
    plt.title(
        "Top 5 Protein-Rich Recipes per Diet Across Cuisines"
        f"\nGenerated {timestamp}"
    )
    plt.xlabel("Cuisine Type")
    plt.ylabel("Protein (g)")
    plt.xticks(rotation=40, ha="right")
    plt.legend(title="Diet Type", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(output_directory / "scatter_top_protein_by_cuisine.png", dpi=300)
    plt.close()


def print_results(
    dataframe: pd.DataFrame,
    missing_before: dict[str, int],
    results: dict[str, object],
    output_directory: Path,
    run_time: datetime,
) -> None:
    """Print a readable summary that can be captured for assignment evidence."""
    print("\n" + "=" * 72)
    print("TASK 1: DATASET ANALYSIS AND INSIGHTS")
    print("=" * 72)
    print(f"Analysis started: {run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dataset rows: {len(dataframe):,}")
    print(f"Duplicate rows detected: {int(dataframe.duplicated().sum())}")
    print(f"Missing numeric values before cleaning: {missing_before}")
    print("Missing numeric values after cleaning: 0")

    print("\n1. Average macronutrients by diet type")
    print(results["average_macros"].round(2).to_string(index=False))

    print("\n2. Top 5 protein-rich recipes per diet type")
    print(results["top_five_protein"].round(2).to_string(index=False))

    print("\n3. Diet type with the highest average protein")
    print(
        f"{results['highest_average_diet']} "
        f"({results['highest_average_protein']:.2f} g average protein)"
    )
    print("Highest-protein individual recipe")
    print(
        f"{results['highest_recipe_name']} - {results['highest_recipe_diet']} "
        f"({results['highest_recipe_protein']:.2f} g protein)"
    )

    print("\n4. Most common cuisine for each diet type")
    print(results["most_common_cuisines"].to_string(index=False))

    print("\n5. New ratio metrics")
    print(
        dataframe[
            [
                "Diet_type",
                "Recipe_name",
                "Protein_to_Carbs_ratio",
                "Carbs_to_Fat_ratio",
            ]
        ]
        .head(10)
        .round(3)
        .to_string(index=False)
    )

    print("\nGenerated output files:")
    for output_file in sorted(output_directory.iterdir()):
        print(f"- {output_file.name}")
    print(f"\nAnalysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze the All_Diets.csv dataset.")
    parser.add_argument(
        "--input",
        type=Path,
        default=find_default_dataset(),
        help="Path to All_Diets.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "outputs",
        help="Directory for generated tables and charts",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    run_time = datetime.now()
    output_directory = arguments.output.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    dataframe, missing_before = load_and_clean_data(arguments.input.resolve())
    results = calculate_results(dataframe)
    save_tables(dataframe, results, output_directory)
    save_visualizations(results, output_directory, run_time)
    print_results(dataframe, missing_before, results, output_directory, run_time)


if __name__ == "__main__":
    main()
