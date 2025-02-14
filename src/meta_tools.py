# Standard library imports.
from typing import Tuple, Optional

# Related third party imports.
import pandas as pd

import exiter
# Local application/library specific imports.
from constants.obj_specs import ICOS_OBJECT_SPECS, CITIES_OBJECT_SPECS


def get_spec(reason: str, file_name: str) -> Tuple[str, str]:
    # Todo: reason and data_object_specs should be in a frozen dataclass
    #   in the settings.py file. The ds_type seems not needed, but it is
    #   used in the json_manager.py file to construct the title. It is
    #   only used for cte-hr so perhaps I can find a work around.
    ds_type, obj_spec_uri = None, None
    if reason == 'cte-hr':
        if any(part in file_name for part in ['persector', 'anthropogenic']):
            ds_type = 'Anthropogenic emission model results (near real time)'
            obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
        elif 'nep' in file_name:
            ds_type = 'Biospheric model results (near real time)'
            obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
        elif 'fire' in file_name:
            ds_type = 'Fire emission model results (near real time)'
            obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
        elif 'ocean' in file_name:
            ds_type = 'Oceanic flux model results (near real time)'
            obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
    elif reason in ['lpj-guess-eu', 'lpj-guess-global']:
        ds_type = 'Biosphere modeling spatial result'
        obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
    elif reason == 'cities':
        ds_type = 'Non-standard spatial product'
        obj_spec_uri = CITIES_OBJECT_SPECS[ds_type]
    elif reason == 'cities-fluxes':
        fp = '/srv/git/zupload/input-files/data-files/cities-fluxes/files_to_be_uploaded.xlsx'
        df = pd.read_excel(fp, engine='openpyxl')
        row = df[df['Upload file'] == file_name]
        if row['Object Spec'].iloc[0] == 'https://citymeta.icos-cp.eu/resources/cpmeta/ecFluxArchiveRaw':
            ds_type = 'EC flux time series archive (raw data)'
        elif row['Object Spec'].iloc[0] == 'https://citymeta.icos-cp.eu/resources/cpmeta/ecFluxArchiveL1':
            ds_type = 'EC flux time series archive (L1)'
        obj_spec_uri = CITIES_OBJECT_SPECS[ds_type]
    elif reason == 'lidar':
        ds_type = 'Doppler Wind Lidar vertical wind profile'
        obj_spec_uri = CITIES_OBJECT_SPECS[ds_type]
    elif reason in ['mapbooks', 'stilt-docs']:
        ds_type = 'Easter Egg'
        obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
    elif 'transcom' in file_name:
        ds_type = 'inversion time-series'
        obj_spec_uri = \
            ICOS_OBJECT_SPECS['Inversion modeling time-series result']
    elif any(part in file_name for part in ['CSR', 'LUMIA', 'Priors', 'GCP']):
        ds_type = 'Inversion modeling spatial result'
        obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
    elif 'zip' in file_name:
        if 'PARIS_WP3' in file_name:
            ds_type = 'Atmospheric measurements results archive'
            obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
        else:
            ds_type = 'model data archive'
            obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
    elif any(part in file_name for part in [
        'VPRM', 'lpj', 'ET', 'ET_T', 'GPP', 'NEE'
    ]):
        ds_type = 'Biosphere modeling spatial result'
        obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
    elif 'traceRadon' in file_name:
        ds_type = 'radon flux map'
        obj_spec_uri = \
            ICOS_OBJECT_SPECS['radon_flux_map']
    elif all(part in file_name for part in ['EDGAR', 'CO2']):
        ds_type = 'Emission inventory for CO2'
        obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
    elif all(part in file_name for part in ['EDGAR', 'CH4']):
        ds_type = 'Emission inventory for CH4'
        obj_spec_uri = ICOS_OBJECT_SPECS[ds_type]
    elif 'AVENGERS' in file_name:
        ds_type = 'AVENGERS aerosol emissions'
        obj_spec_uri = \
            ICOS_OBJECT_SPECS['cf_compliant_netcdf']
    elif reason == 'd3.13':
        ds_type = 'Biogenic in-situ observations (L2)'
        obj_spec_uri = CITIES_OBJECT_SPECS[ds_type]

    assert obj_spec_uri is not None, \
        f'Could not infer data type specification for {file_name}'
    assert ds_type is not None, 'Could not infer data type specification'
    return ds_type, obj_spec_uri
