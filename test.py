# %%
from dotenv import load_dotenv
import os
from src.db.song_master.manager import SongMasterManager
from src.db.song_master.constants import SONG_MASTER_LIST_UUID

load_dotenv()

# %%
song_master_manager = SongMasterManager(
    master_file=os.getenv("MASTER_FILE"),
    song_data_folder=os.getenv("SONG_DATA_FOLDER"),
    uuid_seed=SONG_MASTER_LIST_UUID,
)

# %%
dfs = song_master_manager.get_all_songs_snapshot()

# %%
