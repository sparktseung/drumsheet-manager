import pandas as pd
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
        self.uuid_seed = uuid_seed or self._generate_song_master_list_uuid()
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
            df = pd.read_csv(master_file_path)
        elif master_file_path.suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(master_file_path)
        else:
            raise ValueError(
                "Unsupported file format. Please provide a CSV or Excel file."
            )

        # Check if required columns are present
        if not self.REQUIRED_COLUMNS.issubset(df.columns):
            missing_cols = self.REQUIRED_COLUMNS - set(df.columns)
            raise ValueError(
                f"Missing required columns: {', '.join(missing_cols)}"
            )

        # Generate a uuid for each row using the seed uuid
        df["uuid"] = df.apply(
            lambda row: str(
                uuid.uuid5(
                    self.uuid_seed, f"{row['artist_en']}_{row['song_name_en']}"
                )
            ),
            axis=1,
        )

        self.df_song_master_list = df

    def list_all_available_song_data(self) -> pd.DataFrame:
        song_data_root = Path(self.song_data_folder)

        if not song_data_root.exists():
            raise FileNotFoundError(
                f"Song data folder does not exist: {song_data_root}"
            )
        if not song_data_root.is_dir():
            raise NotADirectoryError(
                f"Song data path is not a directory: {song_data_root}"
            )

        df_files = pd.DataFrame(
            [
                {
                    "file_path": file_path,
                    "file_name": file_path.name,
                    "stem": file_path.stem,
                    "extension": file_path.suffix,
                }
                for file_path in song_data_root.rglob("*")
                if file_path.is_file()
            ]
        )

        df_files["artist_en"] = df_files["stem"].apply(
            lambda x: x.split("-")[-2].strip()
        )
        df_files["song_name_en"] = df_files["stem"].apply(
            lambda x: x.split("-")[-1].strip()
        )

        self.df_all_available_song_data = df_files

    def _generate_song_master_list_uuid(self) -> str:
        return str(uuid.uuid4())
