# Standard library imports.
from dataclasses import dataclass
from pathlib import Path
# Related third party imports.
import yaml

import exiter
# Local application/library specific imports.
from constants.general_settings import YAML_SETTINGS


@dataclass()
class YamlSettings:
    portal: str
    reason: str
    archive_files: bool
    try_ingest: bool
    calculate_hash_sum: bool
    archive_json: bool
    upload_meta_data: bool
    upload_data: bool
    primary_dir: str | None
    archive_path: str | None
    json_files: str | None
    json_coll_files: str | None
    data_dir: str
    pattern: str
    previous_collection: str | None
    try_ingest_subprocesses: int
    show_input_files: bool
    show_progress_archive_files: bool
    show_progress_try_ingest: bool
    show_separator: bool
    show_progress_archive_json: bool
    show_progress_hash_sum: bool
    show_progress_upload_meta_data: bool
    show_progress_upload_data: bool
    upload_to_production: bool
    overwrite_archive: bool


class Settings:

    def __init__(self) -> None:
        self.settings = self.read_settings()
        if self.settings.portal not in ['icos', 'cities', 'sites']:
            msg = ('Wrong or no portal defined in file: "settings.yml".'
                   ' Valid entries are "icos", "cities", or "sites"')
            exiter.exit_zupload(info={'msg': msg})
        self.init_files()
        return

    @staticmethod
    def read_settings() -> YamlSettings:
        with open(file=YAML_SETTINGS, mode='r') as yaml_handler:
            return YamlSettings(**yaml.safe_load(yaml_handler))

    def init_files(self) -> None:
        """Create the needed application directories.

        If no `primary_dir` is set in the settings, the application will
        place its generated files under "output/" in the application's
        root directory.
        Specifically in a directory named after the reason of this
        upload.
        """
        r = self.settings.reason
        if not self.settings.primary_dir:
            self.settings.primary_dir = f'output/{r}'
            self.settings.archive_path = f'output/{r}/archive.json'
            self.settings.json_files = f'output/{r}/json-files/'
            self.settings.json_coll_files = f'output/{r}/json-coll-files/'
        Path(self.settings.primary_dir).mkdir(parents=True, exist_ok=True)
        Path(self.settings.archive_path).touch(exist_ok=True)
        Path(self.settings.json_files).mkdir(parents=True, exist_ok=True)
        Path(self.settings.json_coll_files).mkdir(parents=True, exist_ok=True)
