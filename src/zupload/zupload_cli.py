# Standard library imports.
from pathlib import Path
from pprint import pprint
from typing import Any
import json
import ast
# Related third party imports.
import pandas as pd
from openpyxl.pivot.fields import Boolean
from pandas import Series
import typer
import requests
# Local application/library specific imports.
from zupload.utils import calculate_hashsum, get_conf, get_cookie_jar, write_json
from zupload.constants.envri import EnvriConfig


app = typer.Typer(help='Upload data & metadata to the specific portal.')

@app.command()
def main(spreadsheet: str | None = None, extract_json: bool = False, upload: bool = True):
    if extract_json: upload = False
    if spreadsheet is None:
        matches = list(Path.cwd().glob('*.xlsx'))
        if not matches:
            typer.echo('No .xlsx files found in current directory.')
            raise typer.Exit(code=1)
        spreadsheet = matches[0]
    else: spreadsheet = Path(spreadsheet)
    envri_conf = get_conf(file_path=spreadsheet)
    if upload:
        typer.echo(f'Using portal: {envri_conf.envri}')
    df = pd.read_excel(spreadsheet, sheet_name='upload_meta')
    for _, row in df.iterrows():
        meta_json = make_json(meta=row)
        if upload:
            data_url = upload_meta(meta_json=meta_json, envri_conf=envri_conf)
            upload_data(file_path=row['fileLocation'], data_url=data_url)
        else:
            p = Path(row['fileLocation'])
            json_path = p.with_suffix('.json')
            write_json(file=json_path, content=meta_json)
            pprint(meta_json)
            typer.echo(f'JSON written to {json_path}')



def make_json(meta: Series):
    json_meta = dict({
        'fileName': meta['fileName'],
        'hashSum': calculate_hashsum(file_path=meta['fileLocation']),
        'isNextVersionOf': None if pd.isna(meta['isNextVersionOf']) else meta['isNextVersionOf'],
        'preExistingDoi': None if pd.isna(meta['doiURI']) else meta['doiURI'],
        'objectSpecification': meta['objectSpecification'],
        'references': {
            'keywords': json.loads(meta['keywords']),
            'licence': meta['licenseUrl'],
            'autodeprecateSameFilenameObjects': False,
            'duplicateFilenameAllowed': True,
        },
        'specificInfo': {
            'title': meta['title'],
            'description': meta['abstract/description '],
            'spatial': meta['coverageURI'],
            'temporal': {
                'interval': {
                    'start': meta['startCov'],
                    'stop': meta['stopCov'],
                },
                'resolution': meta['resolution'],
            },
            'forStation': None,
            'production': {
                'creator': meta['creatorURI'],
                'contributors': json.loads(meta['contributorURI']),
                'hostOrganization': meta['hostOrganizationURI'],
                'comment': None if pd.isna(meta['comment']) else meta['comment'],
                'sources': [],
                'documentation': None if pd.isna(meta['documentation']) else meta['documentation'],
                'creationDate': meta['created'],
            },
            'variables': json.loads(meta['variables'])
        },
        'submitterId': meta['submitterID'],
    })
    return json_meta


def upload_meta(meta_json: dict[str, Any], envri_conf: EnvriConfig) -> str:
    """Upload metadata package to specified portal."""
    typer.echo(f'Uploading metadata for: {meta_json["fileName"]}', nl=False)
    resp = requests.post(
        url=envri_conf.meta_url,
        json=meta_json,
        cookies=get_cookie_jar()
    )
    if resp.status_code == 200:
        typer.echo(f' -> {resp.text.replace("data", "meta")} ({resp.status_code}) OK')
    else:
        typer.echo(f' ({resp.status_code}) FAILED')
        typer.echo(resp.text)
        raise typer.Exit(code=1)
    return resp.text


def upload_data(file_path: str | Path, data_url: str) -> None:
    """Upload data file to specified portal."""
    file_path = Path(file_path)
    typer.echo(f'Uploading data for: {file_path}', nl=False)
    resp = requests.put(
        url=data_url,
        data=open(file=file_path, mode='rb'),
        cookies=get_cookie_jar(),
        headers={'Content-Type': 'application/octet-stream'},
    )
    if resp.status_code == 200:
        typer.echo(f' -> {resp.text} ({resp.status_code}) OK')
    else:
        typer.echo(f' ({resp.status_code}) FAILED')
        typer.echo(resp.text)
        raise typer.Exit(code=1)
    return


if __name__ == "__main__":
    app()
