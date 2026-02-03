# Standard library imports.
from http.cookiejar import CookieJar
from pathlib import Path
from typing import cast, Any
import hashlib
import json
# Related third party imports.
from icoscp_core import icos, auth
from requests.utils import cookiejar_from_dict
from requests.cookies import RequestsCookieJar, cookiejar_from_dict
import pandas as pd
import typer
# Local application/library specific imports.
from zupload.constants.envri import ENVRIES, EnvriConfig, Envri


def calculate_hashsum(file_path: str | Path) -> str:
    """Calculate and return hash-sum of given file."""
    file_path = Path(file_path)
    sha256_hash = hashlib.sha256()
    total = file_path.stat().st_size
    progress = total > 500 * 1024 * 1024
    with open(file=file_path, mode='rb') as f_hdl:
        current = 0
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f_hdl.read(4096), b''):
            sha256_hash.update(byte_block)
            current += len(byte_block)
    return sha256_hash.hexdigest()


def get_conf(file_path: Path) -> EnvriConfig:
    """Read portal information from spreadsheet."""
    try:
        portal_raw = pd.read_excel(file_path, sheet_name='envri_info')['portal'].iloc[0]
    except Exception as e:
        typer.echo(f'Could not read portal value from "envri_info" sheet: {e}')
        raise typer.Exit(code=1)
    valid_portals = ', '.join(ENVRIES.keys())
    if pd.isna(portal_raw) or str(portal_raw).strip().upper() not in valid_portals:
        typer.echo(f'Invalid or missing portal value "{portal_raw}". Expected one of: {valid_portals}')
        raise typer.Exit(code=1)
    portal_norm = str(portal_raw).strip().upper()
    portal_key = cast(Envri, portal_norm)
    config = ENVRIES[portal_key]
    return config


def get_cookie_jar() -> RequestsCookieJar:
    cookie_string = icos.auth.get_token().cookie_value
    cookie_dict = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookie_string.split('; ')}
    cookie_jar = cookiejar_from_dict(cookie_dict)
    return cookie_jar


def write_json(file: str | Path, content: dict[str, Any]) -> Path:
    """Write dictionary to JSON file."""
    file = Path(file)
    with open(file=file, mode='w+') as json_handle:
        json.dump(content, json_handle, indent=4)
    return file
