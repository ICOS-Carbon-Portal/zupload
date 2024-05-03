# Standard library imports.
from dataclasses import dataclass
from pathlib import Path
# Related third party imports.
import yaml
# Local application/library specific imports.
from constants.general_settings import YAML_SETTINGS


@dataclass(frozen=True)
class YamlSettings:
    reason: str
    archive_files: bool
    try_ingest: bool
    archive_json: bool
    upload_meta_data: bool
    upload_data: bool
    master_dir: str
    archive_path: str
    json_standalone_files: str
    json_collection_standalone_files: str
    data_dir: str
    pattern: str
    previous_collection: str | None
    try_ingest_subprocesses: int
    show_input_files: bool
    show_progress_archive_files: bool
    show_progress_try_ingest: bool
    show_progress_archive_json: bool
    show_progress_upload_meta_data: bool
    show_progress_upload_data: bool
    upload_to_production: bool
    overwrite_archive: bool


class Settings:

    def __init__(self) -> None:
        self.settings = self.read_settings()
        self.init_files()
        return

    @staticmethod
    def read_settings() -> YamlSettings:
        with open(file=YAML_SETTINGS, mode='r') as yaml_handler:
            return YamlSettings(**yaml.safe_load(yaml_handler))

    def init_files(self) -> None:
        Path(self.settings.master_dir).mkdir(parents=True, exist_ok=True)
        Path(self.settings.archive_path).touch(exist_ok=True)
        Path(self.settings.json_standalone_files).mkdir(parents=True,
                                                        exist_ok=True)
        Path(self.settings.json_collection_standalone_files).\
            mkdir(parents=True, exist_ok=True)
