from zupload.constants.envri import ICOS_CONFIG, CITIES_CONFIG


ICOS_OBJECT_SPECS = {
    'Anthropogenic emission model results (near real time)':
        f'{ICOS_CONFIG.meta_resources_prefix}anthropogenicEmissionModelResults',
    'Atmospheric measurements results archive':
        f'{ICOS_CONFIG.meta_resources_prefix}atmoMeasResultsArchive',
    'Biosphere modeling spatial result':
        f'{ICOS_CONFIG.meta_resources_prefix}biosphereModelingSpatial',
    'Biospheric model results (near real time)':
        f'{ICOS_CONFIG.meta_resources_prefix}biosphericModelResults',
    'CF-compliant NetCDF': f'{ICOS_CONFIG.meta_resources_prefix}arbitraryCfNetcdf',
    'Emission inventory for CO2': f'{ICOS_CONFIG.meta_resources_prefix}co2EmissionInventory',
    'Emission inventory for CH4': f'{ICOS_CONFIG.meta_resources_prefix}ch4EmissionInventory',
    'Fire emission model results (near real time)':
        f'{ICOS_CONFIG.meta_resources_prefix}fireEmissionModelResults',
    'Inversion modeling spatial result': f'{ICOS_CONFIG.meta_resources_prefix}inversionModelingSpatial',
    'Inversion modeling time-series result':
        f'{ICOS_CONFIG.meta_resources_prefix}inversionModelingTimeseries',
    'Model data archive': f'{ICOS_CONFIG.meta_resources_prefix}modelDataArchive',
    'Oceanic flux model results (near real time)': f'{ICOS_CONFIG.meta_resources_prefix}oceanicFluxModelResults',
    'Radon flux map': f'{ICOS_CONFIG.meta_resources_prefix}radonFluxSpatialL3',
}

CITIES_OBJECT_SPECS = {
    'Biogenic in-situ observations (L2)': f'{CITIES_CONFIG.meta_resources_prefix}biogenicArchiveL2',
    'Daily phenocam image set': f'{CITIES_CONFIG.meta_resources_prefix}etcPhenocamDaily',
    'Doppler Wind Lidar vertical wind profile': f'{CITIES_CONFIG.meta_resources_prefix}DWLProfiles',
    'EC flux time series archive (L1)': f'{CITIES_CONFIG.meta_resources_prefix}ecFluxArchiveL1',
    'EC flux time series archive (raw data)': f'{CITIES_CONFIG.meta_resources_prefix}ecFluxArchiveRaw',
    'Non-standard spatial product': f'{CITIES_CONFIG.meta_resources_prefix}nonStandardSpatialNetcdf',
}

ALL_OBJECT_SPECS = {**ICOS_OBJECT_SPECS, **CITIES_OBJECT_SPECS}
