import pandas as pd
from pathlib import Path
import uuid

from .constants import SONG_MASTER_LIST_UUID


def generate_song_master_list_uuid_list():
    return str(uuid.uuid4())


def load_song_master_list(
    file_path: str | Path, uuid_seed: str | uuid.UUID = SONG_MASTER_LIST_UUID
) -> pd.DataFrame:
    """
    Load a song master CSV / Excel file.

    Params
    ------
    file_path: str | Path
        The path to the CSV or Excel file containing the song master list.
        At a minimum, the csv should have these columns:
            - artist_en (string): The name of the artist in English.
            - song_name_en (string): The name of the song in English.
        Other columns will also be loaded as metadata.
    uuid_seed: str | uuid.UUID
        A seed uuid to use for generating uuids for each row.
        This should be a fixed uuid to ensure that the same song will always
        have the same uuid across different runs of the function.
    """
    file_path_str = str(file_path)

    if file_path_str.endswith(".csv"):
        df = pd.read_csv(file_path_str)
    elif file_path_str.endswith(".xlsx") or file_path_str.endswith(".xls"):
        df = pd.read_excel(file_path_str)
    else:
        raise ValueError(
            "Unsupported file format. Please provide a CSV or Excel file."
        )

    # Check if required columns are present
    required_columns = {"artist_en", "song_name_en"}
    if not required_columns.issubset(df.columns):
        missing_cols = required_columns - set(df.columns)
        raise ValueError(
            f"Missing required columns: {', '.join(missing_cols)}"
        )

    # Generate a uuid for each row using the seed uuid
    df["uuid"] = df.apply(
        lambda row: str(
            uuid.uuid5(uuid_seed, f"{row['artist_en']}_{row['song_name_en']}")
        ),
        axis=1,
    )

    return df
