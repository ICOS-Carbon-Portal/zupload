# Related third party imports.
import typer
import requests
# Local application/library specific imports.
from zupload.utils import calculate_hashsum, get_conf, get_cookie_jar
from zupload.constants.envri import ICOS_CONFIG


# Todo: DO NOT DELETE THIS CODE BLOCK, it is meant to be integrated
#  somehow.
#  1. Make the necessary changes to the script below to upload the
#     new monthly 5-component collection. Variables that you need to
#     change: description, members, title.
#     Run the script to upload the monthly collection.
#  2. Use the uploadgui afterward to manually upload the new yearly
#     version. For example deprecate the yearly 2023 collection that
#     includes months 01-09 with a yearly 2023 collection that
#     includes months 01-10 or upload a new yearly collection.
#     Current yearly collection:
#       https://meta.icos-cp.eu/collections/rXeiWlhVKiWPyjVSTXX4IszM
#  3. Use the uploadgui to deprecate the full collection found here
#     https://doi.org/10.18160/20Z1-AYJ2 by replacing the newly
#     uploaded yearly collection (2023 (01-10)) or by appending the
#     newly uploaded yearly collection (2024 (01)). Don't forget to
#     fill in the preexisting doi field.
#  4. Update the target url of the doi to the newly uploaded full
#     collection.


app = typer.Typer(help='Handle collection-level operations.')

@app.command()
def main():
    meta_json = {
        'description': 'Monthly collection of hourly CO2 fluxes for 2025-09, containing hourly estimates of biospheric fluxes, anthropogenic emissions (total and per sector), GFAS fire emissions and Jena CarboScope ocean fluxes, all re-gridded to match the resolution of the biospheric fluxes.\n\nNet ecosystem productivity (gross primary production minus respiration). Positive fluxes are emissions, negative mean uptake. These fluxes are the result of the SiB4 (Version 4.2-COS, hash 1e29b25, https://doi.org/10.1029/2018MS001540) biosphere model, driven by ERA5 reanalysis data at a 0.5x0.5 degree resolution. The NEP per plant functional type are distributed according to the high resolution CORINE land-use map (https://land.copernicus.eu/pan-european/corine-land-cover), and aggregated to CTE-HR resolution.\n\nAnthropogenic emissions include contributions from public power, industry, households, ground transport, aviation, shipping, and calcination of cement. Our product does not include carbonation of cement and human respiration. Public power is based on ENTSO-E data (https://transparency.entsoe.eu/), Industry, Ground transport, Aviation, and Shipping is based on Eurostat data (https://ec.europa.eu/eurostat/databrowser/). Household emissions are based on a degree-day model, driven by ERA5 reanalysis data. Spatial distributions of the emissions are based on CAMS data (https://doi.org/10.5194/essd-14-491-2022). Cement emissions are taken from GridFED V.2021.3 (https://zenodo.org/record/5956612#.YoTmvZNBy9F).\n\nGFAS fire emissions (https://doi.org/10.5194/acp-18-5359-2018), re-gridded to match the resolution of the biosphere, fossil fuel, and ocean fluxes of the CTE-HR product. Please always cite the original GFAS data when using this file, and use the original data when only fire emissions are required. For more information, see https://doi.org/10.5281/zenodo.6477331 Contains modified Copernicus Atmosphere Monitoring Service Information [2020].\n\nOcean fluxes, based on a climatology of Jena CarboScope fluxes (https://doi.org/10.17871/CarboScope-oc_v2020, https://doi.org/10.5194/os-9-193-2013). An adjustment, based on windspeed and temperature, is applied to obtain hourly fluxes at the CTE-HR resolution. Positive fluxes are emissions and negative fluxes indicate uptake. Please always cite the original Jena CarboScope data when using this file, and use the original data when only low resolution ocean fluxes are required.\n\nFor more information, see https://doi.org/10.5281/zenodo.6477331',
        'members': [
                'https://meta.icos-cp.eu/objects/Y9BfUhqI7JLokt90qYHXks4A',
                'https://meta.icos-cp.eu/objects/dtCZCsd52G9ek1aP7-bVk4EG',
                'https://meta.icos-cp.eu/objects/qD5j3cJkm1hMav9dgVXLC7dC',
                'https://meta.icos-cp.eu/objects/NKOCbTckn91SszUEkcF7gbm3',
                'https://meta.icos-cp.eu/objects/WNC3p8JJm34iGiqzJjJR4J0T'
            ],
            'submitterId': 'CP',
            'title': 'High-resolution, near-real-time fluxes over Europe from CTE-HR for 2025-09',
            'isNextVersionOf': None
        }
    typer.echo(f'Uploading collection', nl=False)
    envri_conf = ICOS_CONFIG
    resp = requests.post(
        url=envri_conf.meta_url,
        json=meta_json,
        cookies=get_cookie_jar()
    )
    if resp.status_code == 200:
        typer.echo(f' -> {resp.text} ({resp.status_code}) OK')
    else:
        typer.echo(f' ({resp.status_code}) FAILED')
        typer.echo(resp.text)
        raise typer.Exit(code=1)

