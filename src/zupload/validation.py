import json
from pathlib import Path
from typing import Any

import pandas as pd
from pandas import Series

from zupload.constants.object_specs import ALL_OBJECT_SPECS


REQUIRED_COLUMNS = [
    'fileName',
    'fileLocation',
    'isNextVersionOf',
    'doiURI',
    'objectSpecification',
    'keywords',
    'licenseUrl',
    'title',
    'startCov',
    'stopCov',
    'creatorURI',
    'contributorURI',
    'hostOrganizationURI',
    'comment',
    'created',
    'submitterID',
]


OPTIONAL_COLUMNS = [
    'abstract/description ',
    'coverageURI',
    'documentationURI',
    'hashSum',
    'forStation',
    'variablesToIngest',
    'resolution',
]


def validate_columns(df) -> list[tuple[str, str]]:
    """Report upload_meta columns that make_json requires but are absent from the sheet."""
    issues: list[tuple[str, str]] = []
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            issues.append(('error', f'{column} column is missing from the upload_meta sheet'))
    for column in OPTIONAL_COLUMNS:
        if column == 'abstract/description ':
            if (
                'abstract/description ' not in df.columns
                and 'abstract/description' not in df.columns
            ):
                issues.append((
                    'warning',
                    'abstract/description column is optional and is missing from the upload_meta sheet',
                ))
        elif column not in df.columns:
            issues.append((
                'warning',
                f'{column} column is optional and is missing from the upload_meta sheet',
            ))
    return issues


def validate_row(row: Series) -> list[tuple[str, str]]:
    """Check one upload_meta row and return issues without raising."""
    issues: list[tuple[str, str]] = []

    def is_blank(value: Any) -> bool:
        if pd.isna(value):
            return True
        return not str(value).strip()

    required_fields = [
        'fileName',
        'title',
        'objectSpecification',
        'submitterID',
        'created',
        'keywords',
        'contributorURI',
    ]
    for field in required_fields:
        if field in row and is_blank(row.get(field)):
            issues.append(('error', f'{field} is required and is blank'))

    expected_fields = [
        'creatorURI',
        'hostOrganizationURI',
        'startCov',
        'stopCov',
    ]
    for field in expected_fields:
        if field in row and is_blank(row.get(field)):
            issues.append(('warning', f'{field} is blank'))

    if 'licenseUrl' in row and is_blank(row.get('licenseUrl')):
        issues.append(('warning', 'licenseUrl is blank; the portal will assign its default licence'))

    if not is_blank(row.get('keywords')):
        try:
            parsed = json.loads(str(row.get('keywords')))
            if not isinstance(parsed, list):
                issues.append(('error', 'keywords is not a JSON list'))
        except (ValueError, TypeError):
            issues.append(('error', 'keywords is not valid JSON'))

    if not is_blank(row.get('contributorURI')):
        try:
            parsed = json.loads(str(row.get('contributorURI')))
            if not isinstance(parsed, list):
                issues.append(('error', 'contributorURI is not a JSON list'))
        except (ValueError, TypeError):
            issues.append(('error', 'contributorURI is not valid JSON'))

    if not is_blank(row.get('variablesToIngest')):
        try:
            json.loads(str(row.get('variablesToIngest')))
        except (ValueError, TypeError):
            issues.append(('error', 'variablesToIngest is not valid JSON'))

    if not is_blank(row.get('coverageURI')):
        coverage_raw = str(row.get('coverageURI')).strip()
        if not coverage_raw.startswith(('http://', 'https://')):
            try:
                json.loads(coverage_raw)
            except (ValueError, TypeError):
                issues.append((
                    'error',
                    'coverageURI is neither a URI nor valid JSON'
                ))

    if not is_blank(row.get('objectSpecification')):
        spec = str(row.get('objectSpecification')).strip()
        if spec not in ALL_OBJECT_SPECS.values():
            issues.append(('error', 'objectSpecification is not a known spec URI'))

    uri_fields = [
        'creatorURI',
        'hostOrganizationURI',
        'licenseUrl',
        'isNextVersionOf',
        'doiURI',
        'documentationURI',
    ]
    for field in uri_fields:
        if not is_blank(row.get(field)):
            value = str(row.get(field)).strip()
            if not value.startswith(('http://', 'https://')):
                issues.append(('warning', f'{field} does not look like a URI'))

    date_fields = ['created', 'startCov', 'stopCov']
    parsed_dates: dict[str, Any] = {}
    for field in date_fields:
        if not is_blank(row.get(field)):
            parsed = pd.to_datetime(row.get(field), errors='coerce')
            if pd.isna(parsed):
                issues.append(('warning', f'{field} is not a valid date'))
            else:
                parsed_dates[field] = parsed
    if 'startCov' in parsed_dates and 'stopCov' in parsed_dates:
        if parsed_dates['startCov'] > parsed_dates['stopCov']:
            issues.append(('warning', 'startCov is after stopCov'))

    if is_blank(row.get('hashSum')):
        if not is_blank(row.get('fileLocation')) and not is_blank(row.get('fileName')):
            data_path = Path(str(row.get('fileLocation'))) / str(row.get('fileName'))
            if not data_path.exists():
                issues.append((
                    'warning',
                    'hashSum is blank and no local data file to hash'
                ))

    return issues


def validate_dataframe(df) -> list[dict[str, Any]]:
    """Validate every row and return structured results without printing."""
    results: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        results.append({
            'row': idx + 2,
            'fileName': row['fileName'],
            'issues': validate_row(row=row),
        })
    return results
