from pathlib import Path

import exiter
from settings import Settings
from json_manager import read_json, write_json
from typing import Any
import utils
from constants.envri import ICOS_CONFIG, CITIES_CONFIG, SITES_CONFIG


def make_collection():
    return


def upload_collection(json_file: str, portal: str) -> Any:
    # Todo: Sync this with portal_interactor.py upload_collection().
    url = None
    if portal == 'icos':
        url = ICOS_CONFIG.meta_url
    elif portal == 'cities':
        url = CITIES_CONFIG.meta_url
    elif portal == 'sites':
        url = SITES_CONFIG.meta_url
    else:
        exiter.exit_zupload(info={'msg': f'Not a valid portal: {portal}'})
    response = utils.handle_request(
        request='post',
        args={
            'url': url,
            'data': open(file=json_file, mode='rb'),
            'headers': {'Content-Type': 'application/json'},
            'cookies': utils.get_cookie_jar()
            }
    )
    if response.status_code == 200:
        print(response.text)
    else:
        print(response.status_code,
              response.text)
        exiter.exit_zupload(
            exit_type='upload_meta_data',
            info=dict({
                'status_code':
                    response.status_code,
                'text': response.text,
                'file_name': json_file
            })
        )
    return response.text


if __name__ == '__main__':
    settings = Settings().settings
    archive = read_json(settings.archive_path)
    members = []
    for base_key, base_info in archive.items():
        members.append(base_info['file_metadata_url'])
    json_content = {
        "title": "todo",
        "description": (
            "todo"
        ),
        "members": members,
        "submitterId": "CP",
        "isNextVersionOf": "todo or empty",
        "preExistingDoi": "todo or empty",
        "documentation": "todo or empty"
    }
    file_path = Path(settings.json_collection_standalone_files,
                     f"todo")
    write_json(path=str(file_path.resolve()), content=json_content,
               convert_posix=False)
    # Critical section
    # upload_collection(json_file=str(file_path.resolve()), portal='cities')
    # End of critical section.