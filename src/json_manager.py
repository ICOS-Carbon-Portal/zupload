# Standard library imports.
from datetime import datetime
from typing import Any, Optional, Union, Pattern
import hashlib
import json
from pathlib import Path, PosixPath
import re
# Related third party imports.
import xarray
from xarray.core.dataset import Dataset as XarrayDataset
from icoscp_core.sparql import SparqlResults
from icoscp_core.queries.dataobjlist import DataObjectLite
from icoscp_core.envri import ICOS_CONFIG
import PyPDF2
# Local application/library specific imports.
from constants.licences import ICOS_LICENSE
from constants.icons import ICON_CHECK
from constants.people import *
from constants.static_meta_paths import *
from constants.organizations import *
from constants.spatial_boxes import *
from constants.general_settings import EXCLUDED_VARIABLES
from settings import YamlSettings
from icoscp_core import icos, metaclient, metacore
from icoscp_core.metacore import DocObject
import exiter


class JsonManager:

    def __init__(self, settings: YamlSettings) -> None:
        self.settings = settings

    # Todo: Maybe multi-process this.
    def archive_json(self) -> None:
        """Generates standalone .json files and adds to archive.

        Generates the standalone .json file for each data file and updates
        the archive with the regenerated json content. This function needs
        to be rerun each time we need to change something in the meta-data.
        If we decide to rerun this then it is mandatory that we also
        overwrite the `archive_in_nc.json` file using the function
        `store_current_archive()` at the end of the script.

        """
        print('- Archiving meta-data (Includes hash-sum calculation.)')

        self.make_docs_json() if self.settings.reason == 'stilt-docs' \
            else self.make_json()

    def make_json(self) -> None:
        archive = read_json(self.settings.archive_path)
        for base_key, base_info in archive.items():
            xarray_dataset = xarray.open_dataset(base_info['file_path'])
            hash_sum = get_hash_sum(file_path=base_info['file_path'],
                                    progress=False)
            base_info['json'] = dict({
                'fileName': base_info['file_name'],
                'hashSum': hash_sum,
                'isNextVersionOf': get_previous_version(
                    reason=self.settings.reason,
                    dobj=f'{ICOS_CONFIG.meta_instance_prefix}'
                         f'objects/{hash_sum}',
                    file_name=base_info['file_name']
                ),
                'preExistingDoi': get_doi(reason=self.settings.reason),
                'objectSpecification': base_info['dataset_object_spec'],
                'references': {
                    'keywords': get_keywords(reason=self.settings.reason,
                                             dataset=xarray_dataset),
                    'licence': ICOS_LICENSE,
                },
                'specificInfo': {
                    'description':
                        get_description(
                            reason=self.settings.reason,
                            extra_meta={'dataset': xarray_dataset}
                        ),
                    'production': {
                        'contributors':
                            get_contributors(reason=self.settings.reason),
                        'creationDate':
                            get_creation_date(reason=self.settings.reason,
                                              dataset=xarray_dataset),
                        'creator': get_creator(reason=self.settings.reason),
                        'hostOrganization':
                            get_host_org(reason=self.settings.reason),
                        # Todo: rework this for future cte-hr versions.
                        'comment': get_comment(reason=self.settings.reason,
                                               file_name=base_info[
                                                   'file_name']),
                        'sources': [],
                        'documentation':
                            get_documentation(reason=self.settings.reason),
                    },
                    'spatial': get_spatial_box(
                        reason=self.settings.reason,
                        file_name=base_info['file_name'],
                        dataset=xarray_dataset),
                    'temporal': {
                        'interval': {
                            'start': xarray_dataset.time[0].dt.strftime(
                                '%Y-%m-%dT%H:%M:%SZ').item(),
                            'stop': xarray_dataset.time[-1].dt.strftime(
                                '%Y-%m-%dT%H:%M:%SZ').item(),
                        },
                        'resolution':
                            get_resolution(reason=self.settings.reason,
                                           file_name=base_info['file_name'],
                                           dataset=xarray_dataset),
                    },
                    'title': get_title(reason=self.settings.reason,
                                       extra_meta={
                                           'base_info': base_info,
                                           'dataset': xarray_dataset
                                       }),
                    'variables': [
                        variable for variable in xarray_dataset.data_vars
                        if variable not in EXCLUDED_VARIABLES
                    ]
                },
                'submitterId': 'CP',
            })
            base_info['json_file_path'] = \
                Path(self.settings.json_standalone_files,
                     f'{base_key}.json')
            write_json(base_info['json_file_path'], base_info['json'],
                       convert_posix=False)
            self.maybe_show_progress_archive_json(base_info['file_name'])
        self.maybe_save_archive(archive)

    def make_docs_json(self) -> None:
        archive = read_json(self.settings.archive_path)
        for i, (base_key, base_info) in enumerate(archive.items(), start=1):
            print(f'\t{i}. {base_key}')
            hash_sum = get_hash_sum(file_path=base_info['file_path'],
                                    progress=False)
            prev_version = get_previous_version(
                reason=self.settings.reason,
                dobj=f'{ICOS_CONFIG.meta_instance_prefix}objects/{hash_sum}',
                file_name=base_info['file_name']
            )
            base_info['json'] = dict({
                'authors': [CARBON_PORTAL],
                'title': get_title(
                    reason=self.settings.reason,
                    extra_meta={'prev_version': prev_version,
                                'file_path': base_info['file_path']}
                ),
                'description': get_description(
                    reason=self.settings.reason,
                    extra_meta={
                        'prev_version': prev_version,
                        'file_path': base_info['file_path'],
                    }),
                'fileName': base_info['file_name'],
                'hashSum': hash_sum,
                'isNextVersionOf': prev_version if prev_version else [],
                'references': {
                    'licence': ICOS_LICENSE
                },
                'submitterId': 'CP',
            })
            base_info['json_file_path'] = \
                Path(self.settings.json_standalone_files, f'{base_key}.json')
            write_json(base_info['json_file_path'], base_info['json'])
            self.maybe_show_progress_archive_json(base_info['file_name'])
        self.maybe_save_archive(archive)
        return

    def maybe_save_archive(self, archive: dict[str, Any]) -> None:
        if Path(self.settings.archive_path).exists() and \
                self.settings.overwrite_archive:
            write_json(self.settings.archive_path, archive)

    def maybe_show_progress_archive_json(self, file_name: str) -> None:
        if self.settings.show_progress_archive_json:
            print(f'\t\tSuccessfully archived json for '
                  f'{file_name} {ICON_CHECK}')

    def show_uploads(self) -> None:
        print('- Showing uploaded landing pages.')
        archive = read_json(self.settings.archive_path)
        for base_key, base_info in archive.items():
            if 'file_metadata_url' in base_info:
                # Todo: find a way to check if data is there and add
                #  an additional check here. Unfortunately,
                #  requests.head does not work. 'Allow headers' is
                #  something an administrator must allow.
                print(f'\t{base_info["file_metadata_url"]}')
            else:
                print(f'\tnothing to show for {base_key}')
        return


def get_previous_version(
        reason: str,
        by: str | None = None,
        dobj: Optional[str | DataObjectLite] = None,
        file_name: Optional[str] = None,
) -> str | None:
    """
    TODO: MAKE THIS RETURN STR OR NONE
    Fetch the previous version of a data object.

    :param reason: Todo.
    :type reason: str
    :param by: How to fetch the previous version. Can be 'meta' or
      'name'.
    :type by: str
    :param dobj: Todo.
    :type dobj: str or DataObjectLite or None
    :param file_name: Todo.
    :type file_name: str or None
    :raise TypeError: If the function is missing required keyword
      arguments.
    :return: A tuple containing the landing page of the previous
      version and a single-element list containing the PID of the
       previous version. The tuple can be empty (None, []) if no
       previous version was found.
    :rtype: str | None

    """
    prev_version = None
    if reason == 'stilt-docs' and file_name is not None:
        if file_name == 'SMR017_STILT_station_characterization_2020.pdf':
            file_name = 'SMR017_STILT_station_characterization_2019.pdf'
        with open('queries/find_doc_by_name.txt', mode='r') as q_handle:
            query = q_handle.read().replace('#file_name', file_name)
        sparql_res: SparqlResults = icos.meta.sparql_select(query=query)
        if sparql_res.bindings:
            prev_uri = sparql_res.bindings[0]['doc'].uri
            prev_version = prev_uri.split('/')[-1]
    elif (by is None or by == 'meta') and dobj:
        try:
            dobj = icos.meta.get_dobj_meta(dobj=dobj)
        except Exception as e:
            if 'HTTP response code: 500' in str(e):
                pass
            else:
                raise e
        else:
            prev_version = (
                dobj.previousVersion,
                dobj.previousVersion.split('/')[-1]
                if dobj.previousVersion else None)
    elif (by is None or by == 'meta') and dobj is None:
        # Todo: put exceptions in exceptions.py file.
        raise TypeError('get_previous_version() is missing 1 required keyword'
                        ' argument: "dobj"')
    if prev_version is None:
        print(f'\t\tWarning! Previous version for {file_name} was not found!')
    return prev_version[0]


def get_hash_sum(file_path: str, progress: bool = True) -> str:
    """Calculate and return hash-sum of given file."""
    sha256_hash = hashlib.sha256()
    with open(file=file_path, mode='rb') as file_handle:
        total = int(Path(file_path).stat().st_size)
        # total = int(os.stat(file_path).st_size)
        current = int()
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: file_handle.read(4096), b''):
            sha256_hash.update(byte_block)
            current += len(byte_block)
            # Printing out the progress bar while calculating a
            # hash-sum of a big file is a strenuous task; thus limit
            # the output using multiples of 4096 and when all bytes
            # are read.
            if (current % 65535 == 0 or current == total) and progress:
                progress_bar(
                    operation='calculate_hash_sum', current=current,
                    total=total,
                    info=dict({
                        'file_name': file_path.split('/')[-1]
                    }))
    return sha256_hash.hexdigest()


def get_doi(reason: str) -> str | None:
    pre_existing_doi = None
    if reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-nee', 'fluxcom-gpp']:
        pre_existing_doi = '10.18160/5NZG-JMJE'
    elif reason == 'cte-hr':
        pre_existing_doi = '10.18160/20Z1-AYJ2'
    else:
        print('\t\tWarning! pre-existing-DOI field is empty!')
    return pre_existing_doi


def get_keywords(reason: str, dataset: XarrayDataset) -> list[str | None]:
    keywords: list[str | None] = []
    if reason == 'cte-hr':
        keywords = ['carbon flux']
    elif reason == 'avengers':
        keywords = ['AVENGERS', 'aerosols']
    elif reason == 'cte-gcp':
        keywords = dataset.keywords.split(', ')
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        keywords = dataset.keywords + ['FLUXCOM', 'FLUXCOM-X']
    else:
        print('\t\tWarning! Keywords field is empty!')
    return keywords


# Todo: extra_meta should be the only argument. Integrate the dataset
#  argument in extra_meta.
def get_description(reason: str,
                    extra_meta: dict[Any, Any],
                    dataset: XarrayDataset | None = None) -> Optional[str]:
    description = str()
    if reason == 'stilt-docs':
        with open(STILT_DOCUMENTS_DESCRIPTION, 'r') as file_handle:
            static_description = file_handle.read()
        stilt_id = extra_meta['file_path'].name.split('_')[0]
        pattern = re.compile(r'(\d{2}:\d{2})(.*)( station char)')
        station = extract_meta(extra_meta['file_path'], pattern)
        if extra_meta['prev_version']:
            url = f'{ICOS_CONFIG.meta_instance_prefix}objects/' \
                  f'{extra_meta["prev_version"]}'
            doc_obj = metaclient._get_json_meta(url=url, data_class=DocObject)
            obj_desc = doc_obj.description
            lat_group = re.search(r'(Latitude: )(.{3,5})( deg)', obj_desc)
            lat = lat_group[2] if lat_group else None
            lon_group = re.search(r'(Longitude: )(.{3,5})( deg)', obj_desc)
            lon = lon_group[2] if lon_group else None
            alt_group = re.search(r'(above ground: )(\d{1,3})', obj_desc)
            alt = alt_group[2] if alt_group else None
        else:
            print('\t\tWarning! cannot retrieve description parts from '
                  'previous version, trying from the input data file '
                  'itself...')
            lat_pat = re.compile(r'(latitude: )(.{3,5})')
            lat = extract_meta(extra_meta['file_path'], lat_pat)
            lon_pat = re.compile(r'(longitude:\s)(.{3,5})')
            lon = extract_meta(extra_meta['file_path'], lon_pat)
            alt_pat = re.compile(r'(Model height: )(.{1,3})(m)')
            alt = extract_meta(extra_meta['file_path'], alt_pat)
        # Todo: Mypy does not like:
        #  any(x is None for x in [station, lat, lon, alt]):
        if station is None or lat is None or lon is None or alt is None:
            print(f'Detected None value, see below for more info.\n'
                  f'station: {station}\n'
                  f'stilt id: {stilt_id}\n'
                  f'lat: {lat}\n'
                  f'lon: {lon}\n'
                  f'alt: {alt}\n------')
            exiter.exit_zupload(exit_type='todo')
        else:
            description = static_description.\
                replace('_station_name_', station).\
                replace('_stilt_id_', stilt_id).\
                replace('_lat_', lat).\
                replace('_lon_', lon).\
                replace('_alt_', alt)
    elif reason == 'cte-hr' and 'dataset' in extra_meta:
        description = extra_meta['dataset'].comment
    elif reason == 'avengers':
        description = (
            'This aerosol emission dataset is based on the CAMS-REG '
            'inventory version 5 (Kuenen et al, 2022, '
            'https://doi.org/10.5194/essd-14-491-2022) but modified '
            'to include the contribution from the condensable PM '
            'fraction for residential wood/coal combustion in a '
            'consistent way, as outlined in Denier van der Gon et '
            'al. (2015, https://doi.org/10.5194/acp-15-6503-2015). '
            'This dataset is prepared by TNO for the AVENGERS '
            'project in such a way that it can be directly nested '
            'in the HTAPv3 dataset (Crippa et al., 2023, '
            'https://doi.org/10.5194/essd-15-2667-2023)'
        )
    elif reason == 'cte-gcp' and dataset:
        description = (
            f'{dataset.summary}\n\n{dataset.source}\n\n{dataset.references}'
        )
    elif reason == 'gcp-inversions':
        description = dataset.summary
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        description = (
            f'{dataset.summary}\n'
            f'\nPublished paper: https://egusphere.copernicus.org/preprints/'
            f'2024/egusphere-2024-165/'
        )
    else:
        print('\t\tWarning! Description field is empty!')
    return description


def get_contributors(reason: str) -> list[str | None]:
    contributors: list[str | None] = []
    if reason == 'cte-hr':
        contributors = \
            [INGRID_LUIJKX, NAOMI_SMITH, REMCO_DE_KOK, WOUTER_PETERS]
    elif reason == 'avengers':
        contributors = [HUGO_DENIER, STIJN_DELLAERT, JEROEN_KUENEN]
    elif reason == 'cte-gcp':
        contributors = [INGRID_LUIJKX, WOUTER_PETERS]
    elif reason == 'gcp-inversions':
        contributors = [WOUTER_PETERS, CHRISTIAN_ROEDENBECK,
                        FREDERIC_CHEVALLIER, ZOE_LLORET, ANNE_COZIC,
                        YOSUKE_NIWA, ANDREW_JACOBSON, JUNJIE_LIU,
                        KEVIN_BOWMAN, JEONGMIN_YUN, BRENDAN_BYRNE,
                        ANTHONY_BLOOM, ZHE_JIN, XIANGJUN_TIAN, SHILONG_PIAO,
                        YILONG_WANG, HONGQIN_ZHANG, MIN_ZHAO, TAO_WANG,
                        JINZHI_DING, BO_ZHENG, ZHIQIANG_LIU, NING_ZENG,
                        FEI_JIANG, WEIMIN_JU, LIANG_FENG, PAUL_PALMER,
                        DONGXU_YANG, NAVEEN_CHANDRA, PRABIR_PATRA]
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        contributors = [SOPHIA_WALTHER, JACOB_NELSON, GREGORY_DUVEILLER,
                        FABIAN_GANS, ZAYD_HAMDI, MARTIN_JUNG, BASIL_KRAFT,
                        ULRICH_WEBER, WEIJIE_ZHANG]
    else:
        print('\t\tWarning! Contributors field is empty!')
    return contributors


def get_creation_date(reason: str, dataset: XarrayDataset) -> Optional[str]:
    creation_date = None
    if reason == 'cte-hr':
        creation_date = datetime \
            .strptime(dataset.creation_date, '%Y-%m-%d %H:%M') \
            .strftime('%Y-%m-%dT%H:%M:%SZ')
    elif reason == 'avengers':
        creation_date = datetime \
            .strptime(dataset.creation_time, '%d/%m/%Y %H:%M:%S') \
            .strftime('%Y-%m-%dT%H:%M:%SZ')
    elif reason in ['cte-gcp', 'gcp-inversions', 'fluxcom-et',
                    'fluxcom-et-t', 'fluxcom-gpp', 'fluxcom-nee']:
        creation_date = datetime \
            .strptime(dataset.creation_date, '%Y-%m-%d') \
            .strftime('%Y-%m-%dT11:00:00Z')
    if not creation_date:
        exiter.exit_zupload(info=dict({'message': 'Creation date cannot be '
                                                  'empty'}))
    return creation_date


def get_creator(reason: str) -> str | list[str] | None:
    creator = None
    if reason == 'cte-hr':
        creator = AUKE_WOUDE
    elif reason == 'avengers':
        creator = HUGO_DENIER
    elif reason == 'cte-gcp':
        creator = REMCO_DE_KOK
    elif reason == 'gcp-inversions':
        creator = INGRID_LUIJKX
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        creator = ULRICH_WEBER
    if not creator:
        exiter.exit_zupload(info=dict({'message': 'Creator cannot be empty'}))
    return creator


def get_host_org(reason: str) -> Optional[str]:
    host_org = None
    if reason in ['cte-hr', 'cte-gcp', 'gcp-inversions']:
        host_org = WUR
    elif reason == 'avengers':
        host_org = TNO
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        host_org = CARBON_PORTAL
    else:
        print('\t\tWarning! Host organization field is empty!')
    return host_org


def get_comment(reason: str, file_name: str) -> Optional[str]:
    comment = None
    if reason == 'cte-hr':
        if file_name in ['anthropogenic.persector.202306.nc',
                         'anthropogenic.202306.nc']:
            comment = (
                'In this version, anthropogenic fluxes have been '
                'corrected to avoid erroneous zero values for on-road'
                ' emissions in Ukraine. Furthermore, a small number of '
                'hours of Public power were found to have zero values '
                'and were replaced with values of the previous hour. '
                'The previous version of this file is missing due to '
                'an error during the upload process. We are sorry for '
                'the inconvenience.'
            )
        elif file_name in \
                ['fire.202306.nc', 'nep.202306.nc', 'ocean.202306.nc']:
            pass
        # else:
        #     comment = (
        #         'In this version, anthropogenic fluxes have been '
        #         'corrected to avoid erroneous zero values for on-road'
        #         ' emissions in Ukraine. Furthermore, a small number of '
        #         'hours of Public power were found to have zero values '
        #         'and were replaced with values of the previous hour.'
        #     )
    return comment


def get_documentation(reason: str) -> Optional[str]:
    documentation = None
    if reason == 'avengers':
        documentation = 'mt_1_l8X7FUhaYtYbFEMCqXL'
    return documentation


def get_spatial_box(reason: str, file_name: str, dataset: XarrayDataset) \
        -> Optional[Union[str, dict[Any, Any]]]:
    spatial_box: Optional[Union[str, dict[Any, Any]]] = None
    if reason == 'cte-hr':
        spatial_box = CTE_HR_BOX
    elif reason == 'cte-gcp':
        if 'transcom' in file_name:
            spatial_box = GLOBAL_BOX
        # Todo: What is this??
        elif 'flux':
            spatial_box = CTE_HR_BOX
    elif reason == 'avengers':
        spatial_box = AVENGERS_BOX
    elif reason == 'gcp-inversions':
        lat_max = dataset.latitude.max().values.item()
        lat_min = dataset.latitude.min().values.item()
        lon_max = dataset.longitude.max().values.item()
        lon_min = dataset.longitude.min().values.item()
        spatial_box = {
            '_type': 'LatLonBox',
            'geo': {
                'coordinates': [[
                    [lon_min, lat_min],
                    [lon_min, lat_max],
                    [lon_max, lat_max],
                    [lon_max, lat_min],
                    [lon_min, lat_min]
                ]],
                'type': 'Polygon'
            },
            'max': {
                'lat': lat_max,
                'lon': lon_max
            },
            'min': {
                'lat': lat_min,
                'lon': lon_min
            }
        }
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        spatial_box = GLOBAL_BOX
    if not spatial_box:
        exiter.exit_zupload(info=dict({
            'message': 'Spatial box cannot be empty'})
        )
    return spatial_box


def get_resolution(reason: str, file_name: str, dataset: XarrayDataset) -> \
        Optional[str]:
    resolution = None
    if reason == 'cte-hr':
        resolution = 'hourly'
    elif reason in ['avengers', 'gcp-inversions']:
        resolution = 'monthly'
    elif reason == 'cte-gcp':
        if 'monthly' in file_name:
            resolution = 'monthly'
        elif 'yearly' in file_name:
            resolution = 'yearly'
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        if dataset.frequency == '1h':
            resolution = 'hourly'
        elif dataset.frequency == '1d':
            resolution = 'daily'
        elif dataset.frequency == '1mo':
            resolution = 'monthly'
    assert resolution is not None
    # if not resolution:
    #     exiter.exit_zupload(info=dict({
    #         'message': 'Resolution cannot be empty'})
    #     )
    return resolution


def get_title(reason: str, extra_meta: dict[Any, Any]) -> str | None:
    title = None
    if reason == 'cte-hr':
        title = (
            'High-resolution, near-real-time fluxes over Europe '
            f'from CTE-HR: {extra_meta["base_info"]["dataset_type"]} '
            f'{extra_meta["base_info"]["year"]}-'
            f'{extra_meta["base_info"]["month"]}'
        )
    elif reason == 'avengers':
        species = extra_meta['base_info']['file_name'].split('_')[3]
        year = extra_meta['base_info']['file_name'].split('_')[2]
        title = f'TNO {species} emission inventory {year} for AVENGERS'
    elif reason in ['cte-gcp', 'gcp-inversions'] and 'dataset' in extra_meta:
        title = extra_meta['dataset'].title
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        regex, variable, frequency = None, None, None
        if 'ET_T' in extra_meta['base_info']['file_name']:
            regex = r'ET_T|_|\.|nc'
            variable = 'transpiration'
        elif 'ET' in extra_meta['base_info']['file_name']:
            regex = r'ET|_|\.|nc'
            variable = 'evapotranspiration'
        elif 'GPP' in extra_meta['base_info']['file_name']:
            regex = r'GPP|_|\.|nc'
            variable = 'gross primary productivity'
        elif 'NEE' in extra_meta['base_info']['file_name']:
            regex = r'NEE|_|\.|nc'
            variable = 'net ecosystem exchange'
        assert regex is not None
        assert variable is not None
        year, degree, frequency = list(
            filter(None, re.split(regex, extra_meta['file_name']))
        )
        if frequency == 'monthly':
            title = f'FLUXCOM-X monthly {variable} on global ' \
                    f'{float(degree)/100} degree grid for {year}'
        elif frequency == 'daily':
            title = f'FLUXCOM-X daily {variable} on global ' \
                    f'{float(degree)/100} degree grid for {year}'
        elif frequency == 'monthlycycle':
            title = f'FLUXCOM-X monthly diurnal cycle of {variable} on' \
                    f' global {float(degree)/100} degree grid for {year}'
    elif reason == 'stilt-docs':
        if extra_meta['prev_version']:
            url = f'{ICOS_CONFIG.meta_instance_prefix}objects/' \
                  f'{extra_meta["base_info"]["prev_version"]}'
            doc_obj = metaclient._get_json_meta(url=url, data_class=DocObject)
            title = doc_obj.references.title
        else:
            print('\t\tWarning! cannot retrieve title from previous version, '
                  'trying from the input data file itself...')
            pdf_file_obj = open(extra_meta['base_info']['file_path'], 'rb')
            page = (PyPDF2.PdfReader(pdf_file_obj)).pages[0].extract_text()
            station_group = re.search(r'(\d{2}:\d{2})(.*)( station char)',
                                      page)
            station = station_group[2] if station_group else None
            alt_group = re.search(r'(\d{1,3})(m)', page)
            alt = alt_group[1] if alt_group else None
            if station and alt:
                title = \
                    f'STILT station characterization for {station} at {alt}m'
    assert title is not None, 'Title cannot be empty'
    return title


def write_json(path: str,
               content: dict[str, Any],
               convert_posix: bool = True) -> None:
    """Write dictionary to json file."""
    if convert_posix:
        posix_to_str(content)
    with open(file=path, mode='w+') as json_handle:
        json.dump(content, json_handle, indent=4)
    return


def read_json(path: str) -> Any:
    """Read dictionary from json file."""
    with open(file=path, mode='r') as json_handle:
        json_data = json.load(json_handle)
    str_to_posix(json_data)
    return json_data


# Todo: refactor this to correctly handle posix paths in dictionaries
#  and dictionaries within dictionaries.
def posix_to_str(content: dict[str, Any]) -> None:
    """Convert PosixPaths to string file paths."""
    if 'file_path' in content:
        content['file_path'] = str(content['file_path'])
    else:
        for key, sub_dict in content.items():
            if 'file_path' in sub_dict:
                sub_dict['file_path'] = str(sub_dict['file_path'])
            if 'json_file_path' in sub_dict:
                sub_dict['json_file_path'] = str(sub_dict['json_file_path'])
    return


# Todo: refactor this to correctly handle posix paths in dictionaries
#  and dictionaries within dictionaries.
def str_to_posix(content: dict[str, Any]) -> None:
    """Convert string file paths to PosixPaths."""
    if 'file_path' in content:
        content['file_path'] = Path(content['file_path'])
    else:
        for key, sub_dict in content.items():
            if 'file_path' in sub_dict:
                sub_dict['file_path'] = Path(sub_dict['file_path'])
            if 'json_file_path' in sub_dict:
                sub_dict['json_file_path'] = Path(sub_dict['json_file_path'])
    return


def make_monthly_cte_hr_collection(collection: dict[Any, Any]) \
        -> dict[Any, Any]:
    year, month = collection["key"][0:4], collection["key"][4:6]
    with open(file=CTE_HR_MONTHLY_DESCRIPTION, mode="r") as file_handle:
        static_description = file_handle.read()
    collection_json = {
        "description": static_description.replace("year_month",
                                                  f"{year}-{month}"),
        "members": collection["members"],
        "submitterId": "CP",
        "title": f"High-resolution, near-real-time fluxes over Europe "
                 f"from CTE-HR for {year}-{month}",
        "isNextVersionOf":
            collection["isNextVersionOf"] if "isNextVersionOf" in
                                             collection.keys()
            else []
    }
    return collection_json


def make_yearly_fluxcom_collection(collection: dict[Any, Any], reason: str) \
        -> dict[Any, Any]:
    variable, year = collection["key"][0:-5], collection["key"][-4:]
    with open(file=FLUXCOM_YEARLY_DESCRIPTION, mode="r") as file_handle:
        static_description = file_handle.read()
    full_text = {
        "ET": "evapotranspiration",
        "ET_T": "transpiration",
        "GPP": "gross primary productivity",
        "NEE": "net ecosystem exchange"
    }
    title = f'FLUXCOM-X-BASE {full_text[variable]} for {year}'
    collection_json = {
        "description":
            static_description.
            replace("_variable_", full_text[variable]).
            replace("_year_", year),
        "members": collection["members"],
        "submitterId": "CP",
        "title": title,
        "isNextVersionOf":
            collection["isNextVersionOf"] if "isNextVersionOf" in
                                             collection.keys()
            else [],
        "preExistingDoi": get_doi(reason=reason)

    }
    return collection_json


def make_all_years_per_var_fluxcom_collection(
        collection: dict[Any, Any],
        reason: str
) -> dict[Any, Any]:
    variable, years = collection["key"][0:-10], collection["key"][-9:]
    with open(file=FLUXCOM_ALL_YEARS_PER_VAR_DESCRIPTION, mode="r") as \
            file_handle:
        static_description = file_handle.read()
    full_text = {
        "ET": "evapotranspiration",
        "ET_T": "transpiration",
        "GPP": "gross primary productivity",
        "NEE": "net ecosystem exchange"
    }
    title = f'FLUXCOM-X-BASE {full_text[variable]} for {years}'
    collection_json = {
        "description":
            static_description.
            replace("_variable_", full_text[variable]).
            replace("_years_", f"{years[0:4]} to {years[5:]}"),
        "members": collection["members"],
        "submitterId": "CP",
        "title": title,
        "isNextVersionOf":
            collection["isNextVersionOf"] if "isNextVersionOf" in
                                             collection.keys()
            else [],
        "preExistingDoi": get_doi(reason=reason)
    }
    return collection_json


def make_yearly_cte_hr_collection(collection: dict[Any, Any]) \
        -> dict[Any, Any]:
    with open(file=CTE_HR_YEARLY_DESCRIPTION, mode="r") as file_handle:
        static_description = file_handle.read()
    collection_json = {
        "description": static_description.replace("year",
                                                  collection["key"]),
        "members": collection["members"],
        "submitterId": "CP",
        "title": f"High-resolution, near-real-time fluxes over Europe from "
                 f"CTE-HR for {collection['key']}",

        "isNextVersionOf":
            collection["isNextVersionOf"] if "isNextVersionOf" in
                                             collection.keys()
            else []
    }
    return collection_json


def make_full_cte_hr_collection(collection: dict[Any, Any]) -> dict[Any, Any]:
    with open(file=CTE_HR_FULL_DESCRIPTION, mode="r") as file_handle:
        static_description = file_handle.read()
    collection_json = {
        "description": static_description,
        "members": collection["members"],
        "submitterId": "CP",
        "title": "High-resolution, near-real-time fluxes over Europe from "
                 "CTE-HR for 2017-2023",
        "isNextVersionOf":
            collection["isNextVersionOf"] if "isNextVersionOf" in
                                             collection.keys()
            else []
    }
    return collection_json


def extract_meta(file_path: PosixPath,
                 pattern: Pattern[str]) -> str | None:
    """Find metadata within an input file using regex."""
    match = None
    if file_path.suffix == '.pdf':
        pdf_file_obj = open(file_path, 'rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file_obj)
        page = pdf_reader.pages[0].extract_text()
        # print(page)
        pdf_file_obj.close()
        group = re.search(pattern, page)
        match = group[2] if group else None
    return match
