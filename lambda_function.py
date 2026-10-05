"""Simulated serverless function for Project 1 Task 3.

The function downloads All_Diets.csv from local Azurite Blob Storage,
calculates average macronutrients for every diet type, and writes the result to
a JSON file that represents local NoSQL document storage.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from azure.storage.blob import BlobServiceClient

from azurite_config import AZURITE_CONNECTION_STRING, BLOB_NAME, CONTAINER_NAME


MACRO_COLUMNS = ["Protein(g)", "Carbs(g)", "Fat(g)"]
REQUIRED_COLUMNS = ["Diet_type", *MACRO_COLUMNS]


def clean_and_calculate_averages(dataframe: pd.DataFrame) -> list[dict[str, object]]:
    """Validate, clean, and calculate average macros per diet type."""
    dataframe.columns = dataframe.columns.str.strip()
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    dataframe["Diet_type"] = (
        dataframe["Diet_type"].astype("string").str.strip().str.lower()
    )
    for column in MACRO_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
        mean_value = dataframe[column].mean()
        if pd.isna(mean_value):
            raise ValueError(f"Column {column} has no usable numeric values.")
        dataframe[column] = dataframe[column].fillna(mean_value)

    averages = (
        dataframe.groupby("Diet_type", as_index=False)[MACRO_COLUMNS]
        .mean()
        .sort_values("Diet_type")
        .round(2)
    )
    return averages.to_dict(orient="records")


def process_nutritional_data_from_azurite(
    output_path: Path | None = None,
) -> dict[str, object]:
    """Download the Blob, process it, and store a local JSON document."""
    if output_path is None:
        output_path = (
            Path(__file__).resolve().parent / "simulated_nosql" / "results.json"
        )
    output_path = output_path.resolve()

    service_client = BlobServiceClient.from_connection_string(
        AZURITE_CONNECTION_STRING
    )
    blob_client = service_client.get_blob_client(
        container=CONTAINER_NAME,
        blob=BLOB_NAME,
    )

    blob_bytes = blob_client.download_blob().readall()
    dataframe = pd.read_csv(io.BytesIO(blob_bytes))
    average_macronutrients = clean_and_calculate_averages(dataframe)

    document = {
        "document_type": "nutritional_insights",
        "source": {
            "storage": "Azurite Blob Storage",
            "container": CONTAINER_NAME,
            "blob": BLOB_NAME,
            "downloaded_bytes": len(blob_bytes),
        },
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
        "recipe_count": int(len(dataframe)),
        "diet_type_count": int(dataframe["Diet_type"].nunique()),
        "average_macronutrients": average_macronutrients,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return document


def main() -> None:
    started_at = datetime.now()
    print("=" * 72)
    print("TASK 3: SIMULATED SERVERLESS NUTRITIONAL DATA PROCESSING")
    print("=" * 72)
    print(f"Function invoked: {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Reading Blob: datasets/All_Diets.csv")

    document = process_nutritional_data_from_azurite()
    result_path = (
        Path(__file__).resolve().parent / "simulated_nosql" / "results.json"
    )

    print(f"Downloaded bytes: {document['source']['downloaded_bytes']:,}")
    print(f"Recipes processed: {document['recipe_count']:,}")
    print(f"Diet types processed: {document['diet_type_count']}")
    print("\nAverage macronutrients calculated from the Azurite Blob:")
    print(
        pd.DataFrame(document["average_macronutrients"]).to_string(index=False)
    )
    print(f"\nSimulated NoSQL document saved: {result_path}")
    print("Data processed and stored successfully.")
    print(f"Function completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
