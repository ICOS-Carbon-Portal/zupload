from constants import envri


cp_meta = envri.ICOS_CONFIG.meta_resources_prefix
# Labels obtained from the Carbon Portal metadata editor.
ICOS_OBJECT_SPECS = {
    'Anthropogenic emission model results (near real time)': f'{cp_meta}anthropogenicEmissionModelResults',
    'Atmospheric measurements results archive': f'{cp_meta}atmoMeasResultsArchive',
    'Biosphere modeling spatial result': f'{cp_meta}biosphereModelingSpatial',
    'Biospheric model results (near real time)': f'{cp_meta}biosphericModelResults',
    'CF-compliant NetCDF': f'{cp_meta}arbitraryCfNetcdf',
    'Emission inventory for CO2': f'{cp_meta}co2EmissionInventory',
    'Emission inventory for CH4': f'{cp_meta}ch4EmissionInventory',
    'Fire emission model results (near real time)': f'{cp_meta}fireEmissionModelResults',
    'Inversion modeling spatial result': f'{cp_meta}inversionModelingSpatial',
    'Inversion modeling time-series result': f'{cp_meta}inversionModelingTimeseries',
    'Model data archive': f'{cp_meta}modelDataArchive',
    'Oceanic flux model results (near real time)': f'{cp_meta}oceanicFluxModelResults',
    'Radon flux map': f'{cp_meta}radonFluxSpatialL3',
    'Easter Egg': 'Easter Egg',
}

# ICOS_OBJECT_SPECS = {
#     'biosphere_modeling_spatial': f'{cp_meta}biosphereModelingSpatial',
#     'anthropogenic_emission_model_results': f'{cp_meta}anthropogenicEmissionModelResults',
#     'biospheric_model_results': f'{cp_meta}biosphericModelResults',
#     'file_emission_model_results': f'{cp_meta}fireEmissionModelResults',
#     'oceanic_flux_model_results': f'{cp_meta}oceanicFluxModelResults',
#     'inversion_modeling_time_series': f'{cp_meta}inversionModelingTimeseries',
#     'inversion_modeling_spatial': f'{cp_meta}inversionModelingSpatial',
#     'model_data_archive': f'{cp_meta}modelDataArchive',
#     'radon_flux_map': f'{cp_meta}radonFluxSpatialL3',
#     'co2_emission_inventory': f'{cp_meta}co2EmissionInventory',
#     'cf_compliant_netcdf': f'{cp_meta}arbitraryCfNetcdf'
# }

city_meta = envri.CITIES_CONFIG.meta_resources_prefix
CITIES_OBJECT_SPECS = {
    'Biogenic in-situ observations (L2)': f'{city_meta}biogenicArchiveL2',
    'Doppler Wind Lidar vertical wind profile': f'{city_meta}DWLProfiles',
    'EC flux time series archive (raw data)': f'{city_meta}ecFluxArchiveRaw',
    'EC flux time series archive (L1)': f'{city_meta}ecFluxArchiveL1',
    'Non-standard spatial product': f'{city_meta}nonStandardSpatialNetcdf',
}
