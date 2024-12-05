# Standard library imports.
from datetime import datetime as dt
from typing import Any, Optional, Union, Pattern
import hashlib
import json
from pathlib import Path, PosixPath
import re
# Related third party imports.
from icoscp_core.envri import ICOS_CONFIG
from icoscp_core.queries.dataobjlist import DataObjectLite
from icoscp_core.sparql import SparqlResults
from xarray.core.dataset import Dataset as Xds
import PyPDF2
import numpy as np
import pyproj
from pyproj import Transformer
import xarray
# Local application/library specific imports.
from constants.colors import Colors as c
from constants.licences import ICOS_LICENSE
from constants.icons import ICON_CHECK
from constants.people import *
from constants.static_meta_paths import *
from constants.stations import *
from constants.organizations import *
from constants.spatial_boxes import *
from constants.general_settings import EXCLUDED_VARIABLES
from settings import YamlSettings
from icoscp_core import icos, cities, metaclient
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
        If we decide to rerun this, then it is mandatory that we also
        overwrite the `archive_in_nc.json` file using the function
        `store_current_archive()` at the end of the script.

        """
        if self.settings.calculate_hash_sum:
            text = '- Archiving meta-data (Includes hash-sum calculation.)'
        else:
            text = '- Archiving meta-data (Hash-sum calculation is excluded.)'
        print(c.color_text(text, c.HEADER, c.BOLD))

        self.make_docs_json() if self.settings.reason == 'stilt-docs' \
            else self.make_json()

    def make_json(self) -> None:
        archive = read_json(self.settings.archive_path)
        for base_key, base_info in archive.items():
            self.maybe_show_separator()
            xrds = xarray.open_dataset(base_info['file_path'])
            if self.settings.calculate_hash_sum:
                hash_sum = get_hash_sum(file_path=base_info['file_path'],
                                        progress=False)
            else:
                hash_sum = base_info['json']['hashSum']

            base_info['json'] = dict({
                'fileName': base_info['file_name'],
                'hashSum': hash_sum,
                'isNextVersionOf': (None if not (
                    p := get_prev_dobj(reason=self.settings.reason,
                                       file_name=base_info[
                                           'file_name'])) else p),
                'preExistingDoi': get_doi(reason=self.settings.reason,
                                          base_info=base_info),
                'objectSpecification': base_info['dataset_object_spec'],
                'references': {
                    'keywords': get_keywords(reason=self.settings.reason,
                                             dataset=xrds),
                    'licence': ICOS_LICENSE,
                    'autodeprecateSameFilenameObjects': False,
                    'duplicateFilenameAllowed': True,
                },
                'specificInfo': {
                    'title': get_title(reason=self.settings.reason,
                                       dataset=xrds, base_info=base_info),
                    'description': get_description(reason=self.settings.reason,
                                                   dataset=xrds,
                                                   base_info=base_info),
                    'spatial': get_spatial_box(reason=self.settings.reason,
                                               file_name=base_info[
                                                   'file_name'], dataset=xrds),
                    'temporal': {
                        'interval': get_interval(reason=self.settings.reason,
                                                 dataset=xrds),
                        'resolution': get_resolution(
                            reason=self.settings.reason,
                            file_name=base_info['file_name'], dataset=xrds),
                    },
                    # 'forStation': (s if (s := get_station(reason=self.settings.reason, base_info=base_info)) else None),
                    'production': {
                        'creator': get_creator(reason=self.settings.reason),
                        'contributors': get_contributors(
                            reason=self.settings.reason),
                        'hostOrganization': get_host_org(
                            reason=self.settings.reason),
                        'comment': (c if (
                            c := get_comment(reason=self.settings.reason,
                                             file_name=base_info['file_name'],
                                             dataset=xrds)) else None),
                        'sources': [],
                        'documentation': (d if (d := get_documentation(
                            reason=self.settings.reason)) else None),
                        'creationDate': get_creation_date(
                            reason=self.settings.reason, dataset=xrds),
                        # Todo: rework this for future cte-hr versions.
                    },

                    'variables': (None if not (
                        v := get_vars(reason=self.settings.reason,
                                      file_name=base_info['file_name'],
                                      dataset=xrds)) else v)
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
                # 'title': get_title(reason=self.settings.reason, extra_meta={'prev_version': prev_version, 'file_path': base_info['file_path']}),
                # 'description': get_description(reason=self.settings.reason, extra_meta={'prev_version': prev_version, 'file_path': base_info['file_path']}),
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

    def maybe_show_separator(self) -> None:
        if self.settings.show_separator:
            print('\t\t---')

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


def get_prev_dobj(
        reason: str | None = None,
        by: str | None = None,
        dobj: Optional[str | DataObjectLite] = None,
        file_name: Optional[str] = None,
) -> str:
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
    prev_version = str()
    # if reason == 'stilt-docs' and file_name is not None:
    #     if file_name == 'SMR017_STILT_station_characterization_2020.pdf':
    #         file_name = 'SMR017_STILT_station_characterization_2019.pdf'
    #     with open('queries/find_doc_by_name.txt', mode='r') as q_hdl:
    #         query = q_hdl.read().replace('#file_name', file_name)
    #     sparql_res: SparqlResults = icos.meta.sparql_select(query=query)
    #     if sparql_res.bindings:
    #         prev_uri = sparql_res.bindings[0]['doc'].uri
    #         prev_version = prev_uri.split('/')[-1]
    # if reason in ['lpj-guess-eu', 'lpj-guess-global'] and file_name:
    #     anchor = f'\tVALUES ?fileName {{ "{file_name}" }}'
    #     prev_version = get_prev_by_name(anchor=anchor)
    if reason == 'cities' and file_name:
        prev_version = get_prev_by_name_cities(anchor=file_name)
    elif reason == 'cte-gcp' and file_name:
        year = int(file_name.split('_')[1].split('GCP')[1])
        prev_file_name = file_name.replace(f'GCP{year}', f'GCP{year - 1}')
        anchor = f'\tFILTER(REGEX(?fileName, "^{prev_file_name}$", "i"))'
        prev_version = get_prev_by_name(anchor=anchor)
    elif reason == 'gcp-inversions' and file_name:
        year = int(file_name.split('_')[0].split('GCP')[1]) - 1
        anchor = f'\tFILTER(REGEX(?fileName, "^GCP{year}_inversions_1x1_version.*.nc$", "i"))'
        prev_version = get_prev_by_name(anchor=anchor)
    elif reason in ['edgar-ch4', 'edgar-co2'] and file_name:
        year = int(file_name.split('_')[1].split('BP')[1]) - 1
        prev_file_name = file_name.replace('BP2024', f'BP{year}')
        anchor = f'\tVALUES ?fileName {{"{prev_file_name}"}}'
        prev_version = get_prev_by_name(anchor=anchor)
    elif dobj:
        prev_version = get_prev_by_dobj(dobj=dobj)

    if not prev_version:
        text = '\t\tWarning! Previous version field is empty!'
        print(c.color_text(text, c.WARNING))
    # elif (by is None or by == 'meta') and dobj:
    #     try:
    #         dobj = icos.meta.get_dobj_meta(dobj=dobj)
    #     except Exception as e:
    #         if 'HTTP response code: 500' in str(e):
    #             pass
    #         else:
    #             raise e
    #     else:
    #         prev_version = (
    #             dobj.previousVersion,
    #             dobj.previousVersion.split('/')[-1]
    #             if dobj.previousVersion else None)
    # elif (by is None or by == 'meta') and dobj is None:
    #     # Todo: put exceptions in exceptions.py file.
    #     raise TypeError('get_previous_version() is missing 1 required keyword'
    #                     ' argument: "dobj"')
    return prev_version
    # if prev_version is None:
    #     print(f'\t\tWarning! Previous version for {file_name} was not found!')
    # return prev_version[0]


def get_prev_by_name_cities(anchor: str) -> str:
    prev_version = str()
    with open('queries/get_prev_by_name_cities.txt', mode='r') as q_hdl:
        query = q_hdl.read().replace('#anchor', anchor)
    sparql_res: SparqlResults = cities.meta.sparql_select(query=query)
    if sparql_res.bindings:
        prev_uri = sparql_res.bindings[0]['dobj'].uri
        prev_version = prev_uri.split('/')[-1]
    return prev_version


def get_prev_by_name(anchor: str) -> str:
    prev_version = str()
    with open('queries/get_prev_by_name_icos.txt', mode='r') as q_hdl:
        query = q_hdl.read().replace('#anchor', anchor)
    print(query)
    sparql_res: SparqlResults = icos.meta.sparql_select(query=query)
    if sparql_res.bindings:
        prev_uri = sparql_res.bindings[0]['dobj'].uri
        prev_version = prev_uri.split('/')[-1]
    return prev_version


def get_prev_by_dobj(dobj: str | DataObjectLite) -> str:
    prev_version = str()
    if ICOS_CONFIG.meta_instance_prefix not in dobj:
        dobj = f'{ICOS_CONFIG.meta_instance_prefix}objects/{dobj}'
    try:
        obj_meta = icos.meta.get_dobj_meta(dobj=dobj)
    except Exception as e:
        if 'HTTP response code: 500' in str(e):
            pass
        else:
            raise e
    else:
        prev_version = obj_meta.previousVersion.split('/')[-1]
    return prev_version


def get_hash_sum(file_path: str, progress: bool = True) -> str:
    """Calculate and return hash-sum of given file."""
    sha256_hash = hashlib.sha256()
    with open(file=file_path, mode='rb') as f_hdl:
        total = int(Path(file_path).stat().st_size)
        # total = int(os.stat(file_path).st_size)
        current = int()
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f_hdl.read(4096), b''):
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


def get_doi(reason: str, base_info: dict[Any, Any]) -> str | None:
    pre_existing_doi = None
    if reason == 'cities':
        if 'zurich' in base_info['file_name']:
            pre_existing_doi = '10.18160/CCV0-XH6P'
        elif 'paris' in base_info['file_name']:
            pre_existing_doi = '10.18160/AVNN-G6Z7'
        elif 'munich' in base_info['file_name']:
            pre_existing_doi = '10.18160/040N-7AP7'
    elif reason == 'cte-hr':
        pre_existing_doi = '10.18160/20Z1-AYJ2'
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-nee',
                    'fluxcom-gpp']:
        pre_existing_doi = '10.18160/5NZG-JMJE'
    elif reason == 'edgar-co2':
        pre_existing_doi = '10.18160/0PM8-KKTS'
    elif reason == 'edgar-ch4':
        pre_existing_doi = '10.18160/MYWZ-NJRY'
    elif reason == 'gcp-inversions':
        pre_existing_doi = '10.18160/KQMP-3AV0'
    elif reason == 'lpj-guess-eu':
        pre_existing_doi = '10.18160/W3N3-9S4D'
    elif reason == 'lpj-guess-global':
        pre_existing_doi = '10.18160/WRN4-1DV6'
    elif reason == 'vprm':
        pre_existing_doi = '10.18160/R5HS-YKW0'

    if not pre_existing_doi:
        text = '\t\tWarning! pre-existing-DOI field is empty!'
        print(c.color_text(text, c.WARNING))
    return pre_existing_doi


def get_keywords(reason: str, dataset: Xds) -> list[str | None]:
    keywords: list[str | None] = []
    if reason == 'avengers':
        keywords = ['AVENGERS', 'aerosols']
    elif reason == 'cities':
        keywords = ['Flux footprints', 'atmospheric modelling', 'urban flux',
                    'ICOS Cities']
    elif reason in ['cte-gcp', 'edgar-ch4', 'edgar-co2']:
        keywords = dataset.keywords.split(', ')
    elif reason == 'cte-hr':
        keywords = ['carbon flux']
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        keywords = dataset.keywords + ['FLUXCOM', 'FLUXCOM-X']
    elif reason in ['lpj-guess-eu', 'lpj-guess-global']:
        keywords = ['LPJ-GUESS', 'Ecosystem model', 'Terrestrial Ecosystem',
                    'Land Biogeochemistry', 'Land Surface', 'Carbon cycle']
    elif reason == 'vprm':
        keywords = ['CO2', 'VPRM']

    if not keywords:
        text = '\t\tWarning! Keywords field is empty!'
        print(c.color_text(text, c.WARNING))
    return keywords


# Todo: extra_meta should be the only argument. Integrate the dataset
#  argument in extra_meta.
def get_description(reason: str,
                    base_info: dict[Any, Any],
                    dataset: Xds | None = None) -> Optional[str]:
    desc = str()
    if reason == 'avengers':
        with open(AVENGERS_DESCRIPTION, 'r') as f_hdl:
            desc = f_hdl.read()
    elif reason == 'cities':
        if 'munich' in base_info['file_name']:
            with open(CITIES_MUNICH_DESCRIPTION, 'r') as f_hdl:
                desc = f_hdl.read()
        elif 'paris' in base_info['file_name']:
            with open(CITIES_PARIS_DESCRIPTION, 'r') as f_hdl:
                desc = f_hdl.read()
        elif 'zurich' in base_info['file_name']:
            with open(CITIES_ZURICH_DESCRIPTION, 'r') as f_hdl:
                desc = f_hdl.read()
    elif reason == 'cte-gcp':
        desc = f'{dataset.summary}\n\n{dataset.source}\n\n{dataset.references}'
    elif reason == 'cte-hr':
        desc = dataset.comment
    elif reason in ['edgar-ch4', 'edgar-co2', 'gcp-inversions']:
        desc = dataset.summary
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        desc = (
            f'{dataset.summary}\n'
            f'\nPublished paper: https://egusphere.copernicus.org/preprints/'
            f'2024/egusphere-2024-165/'
        )
    elif reason == 'lpj-guess-eu':
        with open(LPJ_GUESS_EU_DESCRIPTION, 'r') as f_hdl:
            desc = f_hdl.read()
    elif reason == 'lpj-guess-global':
        with open(LPJ_GUESS_GLOBAL_DESCRIPTION, 'r') as f_hdl:
            desc = f_hdl.read()
    elif reason == 'stilt-docs':
        with open(STILT_DOCUMENTS_DESCRIPTION, 'r') as f_hdl:
            static_desc = f_hdl.read()
        stilt_id = base_info['file_path'].name.split('_')[0]
        pattern = re.compile(r'(\d{2}:\d{2})(.*)( station char)')
        station = extract_meta(base_info['file_path'], pattern)
        if base_info['prev_version']:
            url = f'{ICOS_CONFIG.meta_instance_prefix}objects/' \
                  f'{base_info["prev_version"]}'
            doc_obj = metaclient._get_json_meta(url=url, data_class=DocObject)
            obj_desc = doc_obj.desc
            lat_group = re.search(r'(Latitude: )(.{3,5})( deg)', obj_desc)
            lat = lat_group[2] if lat_group else None
            lon_group = re.search(r'(Longitude: )(.{3,5})( deg)', obj_desc)
            lon = lon_group[2] if lon_group else None
            alt_group = re.search(r'(above ground: )(\d{1,3})', obj_desc)
            alt = alt_group[2] if alt_group else None
        else:
            print('\t\tWarning! cannot retrieve desc parts from '
                  'previous version, trying from the input data file '
                  'itself...')
            lat_pat = re.compile(r'(latitude: )(.{3,5})')
            lat = extract_meta(base_info['file_path'], lat_pat)
            lon_pat = re.compile(r'(longitude:\s)(.{3,5})')
            lon = extract_meta(base_info['file_path'], lon_pat)
            alt_pat = re.compile(r'(Model height: )(.{1,3})(m)')
            alt = extract_meta(base_info['file_path'], alt_pat)
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
            desc = static_desc. \
                replace('_station_name_', station). \
                replace('_stilt_id_', stilt_id). \
                replace('_lat_', lat). \
                replace('_lon_', lon). \
                replace('_alt_', alt)
    elif reason == 'vprm':
        if '2022' in base_info['file_name']:
            with open(VPRM_2022_DESCRIPTION, 'r') as f_hdl:
                desc = f_hdl.read()
        elif '2023' in base_info['file_name']:
            with open(VPRM_2023_DESCRIPTION, 'r') as f_hdl:
                desc = f_hdl.read()

    if not desc:
        text = '\t\tWarning! Description field is empty!'
        print(c.color_text(text, c.WARNING))
    return desc


def get_station(reason: str, base_info: dict[Any, Any]) -> str:
    station = str()
    if reason == 'cities' and 'paris' in base_info['file_name']:
        station = ROMAINVILLE
    elif reason == 'cities' and 'munich' in base_info['file_name']:
        station = OBERPOSTDIREKTION
    elif reason == 'cities' and 'zurich' in base_info['file_name']:
        station = HARDAU
    return station


def get_contributors(reason: str) -> list[str | None]:
    contributors: list[str | None] = []
    if reason == 'avengers':
        contributors = [HUGO_DENIER, STIJN_DELLAERT, JEROEN_KUENEN]
    elif reason == 'cities':
        contributors = [BETTY_MOLINIER, NATASCHA_KLJUN]
    elif reason == 'cte-gcp':
        contributors = [INGRID_LUIJKX, WOUTER_PETERS]
    elif reason == 'cte-hr':
        contributors = \
            [INGRID_LUIJKX, NAOMI_SMITH, REMCO_DE_KOK, WOUTER_PETERS]
    elif reason in ['edgar-ch4', 'edgar-co2']:
        contributors = [CHRISTOPH_GERBIG, THOMAS_KOCH]
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        contributors = [SOPHIA_WALTHER, JACOB_NELSON, GREGORY_DUVEILLER,
                        FABIAN_GANS, ZAYD_HAMDI, MARTIN_JUNG, BASIL_KRAFT,
                        ULRICH_WEBER, WEIJIE_ZHANG]
    elif reason == 'gcp-inversions':
        contributors = [INGRID_LUIJKX, WOUTER_PETERS, CHRISTIAN_ROEDENBECK,
                        FREDERIC_CHEVALLIER, ZOE_LLORET, ADRIEN_MARTINEZ,
                        YOSUKE_NIWA, ANDREW_JACOBSON, JUNJIE_LIU, KEVIN_BOWMAN,
                        JEONGMIN_YUN, BRENDAN_BYRNE, ANTHONY_BLOOM, ZHE_JIN,
                        XIANGJUN_TIAN, SHILONG_PIAO, YILONG_WANG,
                        HONGQIN_ZHANG, MIN_ZHAO, TAO_WANG, JINZHI_DING,
                        ZHIQIANG_LIU, NING_ZENG, FEI_JIANG, WEIMIN_JU,
                        LIANG_FENG, PAUL_PALMER, DONGXU_YANG, NAVEEN_CHANDRA,
                        PRABIR_PATRA, SHAMIL_MAKSYUTOV, LORNA_NAYAGAM,
                        RAJESH_JANARDANAN]
    elif reason in ['lpj-guess-eu', 'lpj-guess-global']:
        contributors = [MICHAEL_MISCHUROW, PAUL_MILLER]
    elif reason == 'vprm':
        contributors = [CHRISTOPH_GERBIG, THOMAS_KOCH]

    if not contributors:
        text = '\t\tWarning! Contributors field is empty!'
        print(c.color_text(text, c.WARNING))
    return contributors


def get_creation_date(reason: str, dataset: Xds) -> str:
    c_date = None
    if reason == 'avengers':
        c_date = dt.strptime(dataset.creation_time, '%d/%m/%Y %H:%M:%S') \
            .strftime('%Y-%m-%dT%H:%M:%SZ')
    elif reason == 'cities':
        d_date = dataset.Date_Created if 'Date_Created' in dataset.attrs \
            else dataset.Creation_Date
        c_date = dt.strptime(d_date, '%d-%b-%Y').strftime('%Y-%m-%dT11:00:00Z')
    elif reason in ['cte-gcp', 'edgar-ch4', 'edgar-co2']:
        c_date = dt.strptime(dataset.creation_date, '%Y-%m-%d') \
            .strftime('%Y-%m-%dT11:00:00Z')
    elif reason == 'cte-hr':
        c_date = dt.strptime(dataset.creation_date, '%Y-%m-%d %H:%M') \
            .strftime('%Y-%m-%dT%H:%M:%SZ')
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        c_date = dt.strptime(dataset.c_date, '%Y-%m-%d') \
            .strftime('%Y-%m-%dT11:00:00Z')
    elif reason == 'gcp-inversions':
        c_date = dt.strptime(dataset.creation_date, '%Y-%m-%d') \
            .strftime('%Y-%m-%dT17:17:51Z')
    elif reason in ['lpj-guess-eu', 'lpj-guess-global']:
        c_date = dt.strptime('2024-06-03', '%Y-%m-%d') \
            .strftime('%Y-%m-%dT11:00:00Z')
    elif reason == 'vprm':
        c_date = dt.strptime(dataset.history[4:24], '%b %d %H:%M:%S %Y') \
            .strftime('%Y-%m-%dT%H:%M:%SZ')

    assert c_date, 'Creation date cannot be empty'
    return c_date


def get_creator(reason: str) -> str:
    creator = None
    if reason == 'avengers':
        creator = HUGO_DENIER
    elif reason == 'cities':
        creator = BETTY_MOLINIER
    elif reason == 'cte-gcp':
        creator = REMCO_DE_KOK
    elif reason == 'cte-hr':
        creator = AUKE_WOUDE
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        creator = ULRICH_WEBER
    elif reason == 'gcp-inversions':
        creator = INGRID_LUIJKX
    elif reason in ['lpj-guess-eu', 'lpj-guess-global']:
        creator = ZHENDONG_WU
    elif reason == 'vprm':
        creator = CHRISTOPH_GERBIG
    elif reason in ['edgar-ch4', 'edgar-co2']:
        creator = THOMAS_KOCH

    assert creator, 'Creator cannot be empty'
    return creator


def get_host_org(reason: str) -> Optional[str]:
    host_org = None
    if reason == 'avengers':
        host_org = TNO
    elif reason == 'cities':
        host_org = LU_AT_CITIES
    elif reason in ['cte-hr', 'cte-gcp', 'gcp-inversions']:
        host_org = WUR
    elif reason in ['edgar-ch4', 'edgar-co2', 'vprm']:
        host_org = MPI_BGC
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee', 'lpj-guess-eu', 'lpj-guess-global']:
        host_org = CARBON_PORTAL

    if not host_org:
        text = '\t\tWarning! Host organization field is empty!'
        print(c.color_text(text, c.WARNING))
    return host_org


def get_comment(reason: str, file_name: str, dataset: Xds | None = None) \
        -> str:
    comment = str()
    if reason == 'cities':
        comment = dataset.Comment
    elif reason == 'cte-hr':
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
    elif reason in ['lpj-guess-eu', 'lpj-guess-global']:
        comment = dataset.summary
    return comment


def get_documentation(reason: str) -> str:
    documentation = str()
    if reason == 'avengers':
        documentation = 'mt_1_l8X7FUhaYtYbFEMCqXL'
    elif reason == 'cities':
        documentation = 'ylBBo5HL8RztF6kb0bHclRQd'
    return documentation


def get_spatial_box(reason: str, file_name: str, dataset: Xds) \
        -> Union[str, dict[Any, Any]]:
    spatial_box: Union[str, dict[Any, Any]] = ''
    if reason == 'avengers':
        spatial_box = AVENGERS_BOX
    elif reason == 'cities':
        tm_proj = pyproj.CRS(dataset.crs_projection4)  # Input CRS
        wgs84_proj = pyproj.CRS('EPSG:4326')  # WGS84 CRS
        transformer = pyproj.Transformer.from_crs(tm_proj, wgs84_proj,
                                                  always_xy=True)
        # Perform the transformation
        lon, lat = transformer.transform(np.array(dataset.x, dtype=np.float32),
                                         np.array(dataset.y, dtype=np.float32))
        # Deprecated code, to be removed.
        # tm_proj = pyproj.Proj(dataset.crs_projection4)
        # wgs84_proj = pyproj.Proj(proj='latlong', datum='WGS84')
        # lon, lat = pyproj.transform(tm_proj, wgs84_proj,
        #                             np.array(dataset.x, dtype=np.float32),
        #                             np.array(dataset.y, dtype=np.float32))
        # End of deprecated code.
        spatial_box = make_spatial_box(lat.min(), lat.max(), lon.min(),
                                       lon.max())
    elif reason == 'cte-hr':
        spatial_box = CTE_HR_BOX
    elif reason == 'cte-gcp':
        if 'transcom' in file_name:
            spatial_box = GLOBAL_BOX
        # Todo: What is this??
        elif 'flux':
            spatial_box = CTE_HR_BOX
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        spatial_box = GLOBAL_BOX
    elif reason == 'gcp-inversions':
        lat_min = dataset.latitude.min().values.item()
        lat_max = dataset.latitude.max().values.item()
        lon_min = dataset.longitude.min().values.item()
        lon_max = dataset.longitude.max().values.item()
        spatial_box = make_spatial_box(lat_min, lat_max, lon_min, lon_max)
    elif reason == 'lpj-guess-eu':
        spatial_box = LPJ_GUESS_EU_BOX
    elif reason == 'lpj-guess-global':
        spatial_box = GLOBAL_BOX
    else:
        spatial_box = make_spatial_box(*extract_coords(dataset))

    assert spatial_box, 'Spatial box cannot be empty'
    return spatial_box


def extract_coords(dataset: Xds) -> list[float]:
    # Todo: make this more general. The variable could either be "lat"
    #  or "latitude" e.t.c.
    lat_min = dataset.lat.min().values.item()
    lat_max = dataset.lat.max().values.item()
    lon_min = dataset.lon.min().values.item()
    lon_max = dataset.lon.max().values.item()
    return [lat_min, lat_max, lon_min, lon_max]


def make_spatial_box(lat_min: float, lat_max: float,
                     lon_min: float, lon_max: float) -> dict[str, Any]:
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
    return spatial_box


def get_interval(reason: str, dataset: Xds) -> dict[str, str]:
    if reason == 'cities':
        start = dt.strptime('20' + str(dataset.timestep[0].item()),
                            '%Y%m%d%H%M').strftime('%Y-%m-%dT%H:%M:%SZ')

        stop = dt.strptime('20' + str(dataset.timestep[-1].item()),
                           '%Y%m%d%H%M').strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        start = dataset.time[0].dt.strftime('%Y-%m-%dT%H:%M:%SZ').item()
        stop = dataset.time[-1].dt.strftime('%Y-%m-%dT%H:%M:%SZ').item()
    return {
        'start': start,
        'stop': stop
    }


def get_resolution(reason: str, file_name: str, dataset: Xds) -> \
        Optional[str]:
    resolution = None
    if reason in ['avengers', 'gcp-inversions']:
        resolution = 'monthly'
    elif reason == 'cities':
        resolution = 'half-hourly'
    elif reason == 'cte-gcp':
        if 'monthly' in file_name:
            resolution = 'monthly'
        elif 'yearly' in file_name:
            resolution = 'yearly'
    elif reason in ['cte-hr', 'edgar-ch4', 'edgar-co2', 'lpj-guess-eu',
                    'lpj-guess-global']:
        resolution = 'hourly'
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        if dataset.frequency == '1h':
            resolution = 'hourly'
        elif dataset.frequency == '1d':
            resolution = 'daily'
        elif dataset.frequency == '1mo':
            resolution = 'monthly'
    elif reason == 'vprm':
        resolution = 'hourly'

    if not resolution:
        text = '\t\tWarning! Resolution field is empty!'
        print(c.color_text(text, c.WARNING))
    return resolution


def get_title(reason: str, dataset: Xds, base_info: dict[Any, Any]) -> str:
    title = str()
    file_name = base_info['file_name']
    if reason == 'avengers':
        species = file_name.split('_')[3]
        year = file_name.split('_')[2]
        title = f'TNO {species} emission inventory {year} for AVENGERS'
    elif reason == 'cities':
        date = dt.strptime(re.split(r'[_\.]', file_name)[2],
                           '%y%m%d').strftime('%Y-%m-%d')
        title = dataset.Title.replace('Daily', 'Diurnal') + f' - {date}'
    elif reason in ['cte-gcp', 'gcp-inversions']:
        title = dataset.title
    elif reason == 'cte-hr':
        title_part = str()
        if 'persector' in base_info['file_name']:
            title_part = 'anthropogenic emissions per sector'
        elif 'anthropogenic' in base_info['file_name']:
            title_part = 'anthropogenic emissions'
        elif 'fire' in base_info['file_name']:
            title_part = 'fire emissions'
        elif 'nep' in base_info['file_name']:
            title_part = 'biospheric fluxes'
        elif 'ocean' in base_info['file_name']:
            title_part = 'ocean fluxes'
        if not title_part:
            text = '\t\tWarning! Part of the title cannot be inferred.'
            print(c.color_text(text, c.WARNING))
        title = (
            'High-resolution, near-real-time fluxes over Europe '
            f'from CTE-HR: {title_part} '
            f'{base_info["year"]}-'
            f'{base_info["month"]}'
        )
    elif reason in ['fluxcom-et', 'fluxcom-et-t', 'fluxcom-gpp',
                    'fluxcom-nee']:
        regex, variable, frequency = None, None, None
        if 'ET_T' in file_name:
            regex = r'ET_T|_|\.|nc'
            variable = 'transpiration'
        elif 'ET' in file_name:
            regex = r'ET|_|\.|nc'
            variable = 'evapotranspiration'
        elif 'GPP' in file_name:
            regex = r'GPP|_|\.|nc'
            variable = 'gross primary productivity'
        elif 'NEE' in file_name:
            regex = r'NEE|_|\.|nc'
            variable = 'net ecosystem exchange'
        assert regex is not None
        assert variable is not None
        year, degree, frequency = list(
            filter(None, re.split(regex, file_name))
        )
        if frequency == 'monthly':
            title = f'FLUXCOM-X monthly {variable} on global ' \
                    f'{float(degree) / 100} degree grid for {year}'
        elif frequency == 'daily':
            title = f'FLUXCOM-X daily {variable} on global ' \
                    f'{float(degree) / 100} degree grid for {year}'
        elif frequency == 'monthlycycle':
            title = f'FLUXCOM-X monthly diurnal cycle of {variable} on' \
                    f' global {float(degree) / 100} degree grid for {year}'
    elif reason in ['lpj-guess-eu', 'lpj-guess-global']:
        var, year = list(
            filter(None,
                   re.split(r'conv_lpj_|_(?:eu|global)_0.5deg_|.nc',
                            file_name))
        )
        title_part = 'European' if reason == 'lpj-guess-eu' else 'Global'
        if var in ['hgpp', 'hnep', 'hnpp']:
            title = f'{title_part} hourly {var[1:].upper()} for {year} ' \
                    f'based on LPJ-GUESS (generated in 2024)'
        elif var == 'hhr':
            title = f'{title_part} hourly heterotrophic respiration for ' \
                    f'{year} based on LPJ-GUESS (generated in 2024)'
        elif var == 'fireC':
            title = f'{title_part} fire disturbance for 2010-2023 based on ' \
                    'LPJ-GUESS (generated in 2024)'
    elif reason == 'stilt-docs':
        if base_info['prev_version']:
            url = f'{ICOS_CONFIG.meta_instance_prefix}objects/' \
                  f'{base_info["prev_version"]}'
            doc_obj = metaclient._get_json_meta(url=url, data_class=DocObject)
            title = doc_obj.references.title
        else:
            print('\t\tWarning! cannot retrieve title from previous version, '
                  'trying from the input data file itself...')
            pdf_file_obj = open(base_info['file_path'], 'rb')
            page = (PyPDF2.PdfReader(pdf_file_obj)).pages[0].extract_text()
            station_group = re.search(r'(\d{2}:\d{2})(.*)( station char)',
                                      page)
            station = station_group[2] if station_group else None
            alt_group = re.search(r'(\d{1,3})(m)', page)
            alt = alt_group[1] if alt_group else None
            if station and alt:
                title = \
                    f'STILT station characterization for {station} at {alt}m'
    elif reason == 'vprm':
        var_map = {
            'GEE': 'gross ecosystem exchange',
            'RESP': 'ecosystem respiration',
            'NEE': 'net ecosystem exchange'
        }
        _, _, var, year, _ = \
            list(filter(None, re.split(r'_|.nc', base_info['file_name'])))
        title = (f'VPRM biosphere model result for {year}: {var_map[var]} '
                 f'of CO2 (generated in 2024)')
    else:
        try:
            title = dataset.title
        except AttributeError as e:
            print(e)

    assert title, 'Title cannot be empty'
    return title


def get_vars(reason: str, file_name: str, dataset: Xds) -> list[str]:
    data_vars: list[str] = []
    if reason == 'cte-gcp' and 'transcom' in file_name:
        pass
    else:
        data_vars: list[str] = [var for var in list(dataset.data_vars)
                                if var not in EXCLUDED_VARIABLES]
    return data_vars


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
    with open(file=CTE_HR_MONTHLY_DESCRIPTION, mode="r") as f_hdl:
        static_description = f_hdl.read()
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
    with open(file=FLUXCOM_YEARLY_DESCRIPTION, mode="r") as f_hdl:
        static_description = f_hdl.read()
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
            f_hdl:
        static_description = f_hdl.read()
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
    with open(file=CTE_HR_YEARLY_DESCRIPTION, mode="r") as f_hdl:
        static_description = f_hdl.read()
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
    with open(file=CTE_HR_FULL_DESCRIPTION, mode="r") as f_hdl:
        static_description = f_hdl.read()
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
