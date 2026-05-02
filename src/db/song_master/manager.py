"""
A SongMasterManager class that looks at and summarizes local raw data.
Compiles a list of available local song data files and compares against an
existing postgres database for syncing.

- Loads a master spreadsheet that contains a list of songs and their metadata.
    - Primary keys: artist_en, song_name_en
    - A uuid is generated for each row using a set seed uuid, based on the two
      primary keys.
- Lists all available song data files in a given folder, and extracts the
  artist and song name from the file name.
    - Naming convention: {anything} - {artist_en} - {song_name_en}.{extension}
    - Each song must have at least a .mp3 and a .pdf file to be valid
    - Optional MuseScore source file .mscz can also be included
"""

import polars as pl
from pathlib import Path
import uuid


class SongMasterManager:

    REQUIRED_COLUMNS = {"artist_en", "song_name_en"}

    def __init__(
        self,
        master_file: str | Path,
        song_data_folder: str | Path,
        uuid_seed: str | uuid.UUID = None,
    ) -> None:
        """
        Params
        ------
        master_file: str | Path
            The path to the CSV or Excel file containing the song master list.
            At a minimum, the csv should have these columns:
                - artist_en (string): The name of the artist in English.
                - song_name_en (string): The name of the song in English.
            Other columns will also be loaded as metadata.
        song_data_folder: str | Path
            The path to the folder where song data (e.g. drum sheet metadata)
            will be stored.
        uuid_seed: str | uuid.UUID
            A seed uuid to use for generating uuids for each row.
            This should be a fixed uuid to ensure that the same song will
            always have the same uuid across different runs of the function.
        """

        self.master_file = master_file
        self.song_data_folder = song_data_folder
        seed = uuid_seed or self._generate_song_master_list_uuid()
        self.uuid_seed = (
            seed if isinstance(seed, uuid.UUID) else uuid.UUID(str(seed))
        )
        self.df_song_master_list = None
        self.df_all_available_song_data = None

    def load_song_master_list(self) -> None:
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
            This should be a fixed uuid to ensure that the same song will
            always have the same uuid across different runs of the function.
        """
        master_file_path = Path(self.master_file)

        if not master_file_path.exists():
            raise FileNotFoundError(
                f"Master file does not exist: {master_file_path}"
            )

        if master_file_path.suffix == ".csv":
            df = pl.read_csv(master_file_path)
        elif master_file_path.suffix in [".xlsx", ".xls"]:
            df = pl.read_excel(master_file_path)
        else:
            raise ValueError(
                "Unsupported file format. Please provide a CSV or Excel file."
            )

        # Check if required columns are present
        if not self.REQUIRED_COLUMNS.issubset(set(df.columns)):
            missing_cols = self.REQUIRED_COLUMNS - set(df.columns)
            raise ValueError(
                f"Missing required columns: {', '.join(missing_cols)}"
            )

        # Generate a deterministic uuid for each row using the seed uuid.
        df = df.with_columns(
            pl.struct(["artist_en", "song_name_en"])
            .map_elements(
                lambda row: str(
                    uuid.uuid5(
                        self.uuid_seed,
                        f"{row['artist_en']}_{row['song_name_en']}",
                    )
                ),
                return_dtype=pl.String,
            )
            .alias("uuid")
        )

        self.df_song_master_list = df

    def list_all_available_song_data(self) -> pl.DataFrame:
        song_data_root = Path(self.song_data_folder)

        if not song_data_root.exists():
            raise FileNotFoundError(
                f"Song data folder does not exist: {song_data_root}"
            )
        if not song_data_root.is_dir():
            raise NotADirectoryError(
                f"Song data path is not a directory: {song_data_root}"
            )

        df_files = pl.DataFrame(
            {
                "file_path": [
                    str(file_path)
                    for file_path in song_data_root.rglob("*")
                    if file_path.is_file()
                ],
            }
        )

        df_files = df_files.with_columns(
            pl.col("file_path")
            .map_elements(
                lambda x: Path(x).name,
                return_dtype=pl.String,
            )
            .alias("file_name"),
            pl.col("file_path")
            .map_elements(
                lambda x: Path(x).stem,
                return_dtype=pl.String,
            )
            .alias("stem"),
            pl.col("file_path")
            .map_elements(
                lambda x: Path(x).suffix,
                return_dtype=pl.String,
            )
            .alias("extension"),
        ).with_columns(
            pl.col("stem")
            .str.split(" - ")
            .list.get(-2)
            .str.strip_chars()
            .alias("artist_en"),
            pl.col("stem")
            .str.split(" - ")
            .list.get(-1)
            .str.strip_chars()
            .alias("song_name_en"),
        )

        self.df_all_available_song_data = df_files
        return self.df_all_available_song_data

    def _generate_song_master_list_uuid(self) -> str:
        return str(uuid.uuid4())
