# Standard library imports.
from http.cookiejar import CookieJar
from pathlib import Path
from typing import cast, Any
import hashlib
import json
import sys
# Related third party imports.
from icoscp_core import icos, cities, auth
from requests.utils import cookiejar_from_dict
from requests.cookies import RequestsCookieJar, cookiejar_from_dict
from halo import Halo
import pandas as pd
import typer
# Local application/library specific imports.
from zupload.constants.envri import ENVRIES, EnvriConfig, Envri

GET_PREV_BY_NAME_QUERY = """
PREFIX cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
SELECT ?dobj
WHERE {
    VALUES ?spec {
        <#spec_anchor>
    }
    ?dobj cpmeta:hasObjectSpec ?spec .
    ?dobj cpmeta:hasName ?fileName .
    FILTER(STRSTARTS(str(?fileName), "#name_anchor"))
    FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
    FILTER EXISTS {?dobj cpmeta:hasSizeInBytes []}
}
"""


def calculate_hashsum(file_path: str | Path, transient: bool = False) -> str:
    """Calculate and return hash-sum of given file."""
    file_path = Path(file_path)
    spinner = Halo(
        text=f'Calculating hashSum for {file_path.name}',
        spinner='dots'
    )
    spinner.start()
    try:
        sha256_hash = hashlib.sha256()
        with open(file=file_path, mode='rb') as f_hdl:
            for byte_block in iter(lambda: f_hdl.read(4096), b''):
                sha256_hash.update(byte_block)
        digest = sha256_hash.hexdigest()
    except Exception:
        spinner.fail(f'Failed to calculate hashSum for {file_path.name}')
        raise
    if transient and sys.stdout.isatty():
        spinner.stop()
        typer.echo(f'\r\033[K✔ Calculated hashSum for {file_path.name}', nl=False)
        return digest
    spinner.succeed(f'Calculated hashSum for {file_path.name}')
    return digest


def get_prev_by_name(
        file_name: str,
        object_spec: str,
        portal: str = 'icos'
) -> str | None:
    portal_norm = portal.strip().lower()
    client = cities if portal_norm in {'cities', 'icoscities'} else icos
    query = GET_PREV_BY_NAME_QUERY \
        .replace('#name_anchor', file_name) \
        .replace('#spec_anchor', object_spec)
    sparql_res = client.meta.sparql_select(query=query)
    if not sparql_res.bindings:
        return None
    prev_uri = sparql_res.bindings[0]['dobj'].uri
    return prev_uri.rsplit('/', 1)[-1]


def get_conf(file_path: Path) -> EnvriConfig:
    """Read portal information from spreadsheet."""
    try:
        portal_raw = pd.read_excel(
            file_path,
            sheet_name='envri_info'
        )['portal'].iloc[0]
    except Exception as e:
        typer.echo(f'Could not read portal value from "envri_info" sheet: {e}')
        raise typer.Exit(code=1)
    if pd.isna(portal_raw):
        typer.echo('Invalid or missing portal value.')
        raise typer.Exit(code=1)
    portal_aliases = {'cities': 'icoscities'}
    portal_norm = portal_aliases.get(str(portal_raw).strip().lower(), str(portal_raw).strip().lower())
    by_lower = {k.lower(): k for k in ENVRIES.keys()}
    if portal_norm not in by_lower:
        typer.echo(
            f'Invalid portal value "{portal_raw}". Expected one of: icos, sites, cities'
        )
        raise typer.Exit(code=1)
    portal_key = cast(Envri, by_lower[portal_norm])
    return ENVRIES[portal_key]


def get_cookie_jar() -> RequestsCookieJar:
    cookie_string = icos.auth.get_token().cookie_value
    cookie_dict = {
        cookie.split('=')[0]: cookie.split('=')[1]
        for cookie in cookie_string.split('; ')
    }
    cookie_jar = cookiejar_from_dict(cookie_dict)
    return cookie_jar


def write_json(file: str | Path, content: dict[str, Any]) -> Path:
    """Write dictionary to JSON file."""
    file = Path(file)
    with open(file=file, mode='w+') as json_handle:
        json.dump(content, json_handle, indent=4)
    return file
