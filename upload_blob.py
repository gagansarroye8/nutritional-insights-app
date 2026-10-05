"""Create the Azurite Blob container and upload All_Diets.csv."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

from azurite_config import AZURITE_CONNECTION_STRING, BLOB_NAME, CONTAINER_NAME


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload All_Diets.csv to the local Azurite Blob service."
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path(__file__).resolve().parent / BLOB_NAME,
        help="Path to All_Diets.csv",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    csv_path = arguments.file.resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    print("=" * 72)
    print("TASK 3: UPLOAD DATASET TO AZURITE BLOB STORAGE")
    print("=" * 72)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Blob endpoint: http://127.0.0.1:10000/devstoreaccount1")

    service_client = BlobServiceClient.from_connection_string(
        AZURITE_CONNECTION_STRING
    )
    container_client = service_client.get_container_client(CONTAINER_NAME)

    try:
        container_client.create_container()
        print(f"Created Blob container: {CONTAINER_NAME}")
    except ResourceExistsError:
        print(f"Blob container already exists: {CONTAINER_NAME}")

    with csv_path.open("rb") as dataset_stream:
        container_client.upload_blob(
            name=BLOB_NAME,
            data=dataset_stream,
            overwrite=True,
        )
    print(f"Uploaded Blob: {CONTAINER_NAME}/{BLOB_NAME}")
    print(f"Source file size: {csv_path.stat().st_size:,} bytes")

    print("\nBlobs currently stored in the container:")
    for blob in container_client.list_blobs():
        print(f"- {blob.name} ({blob.size:,} bytes)")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
