"""Predefined descriptions for recurring upload batches."""

CITIES_UPLOAD_DESCRIPTIONS = {
    'munich': (
        'Daily flux footprints for the Munich-Oberpostdirektion flux-tower in Germany at 30-minute temporal '
        'resolution. Each dataset contains up to 48 footprints with the following variables each: Time, X, Y, '
        'Boundary Layer Height Quality Flag, and Footprint Climatology. The flux footprints are computed using '
        'FFP as described in Kljun et al. (2015), https://doi.org/10.5194/gmd-8-3695-2015, at 10-meter spatial '
        'resolution using ETC L2 Fluxes from Oberpostdirektion, https://hdl.handle.net/11676/WNOldo0yJzYBwDyrywI3oQaX. The projection can be '
        'customized, but the footprints were calculated in UTM 32N. This work is part of the ICOS Cities/PAUL '
        'Pilot Applications in Urban Landscapes project.'
    ),
    'paris': (
        'Daily flux footprints for the Paris-Romainville flux-tower in France at 30-minute temporal resolution. '
        'Each dataset contains up to 48 footprints with the following variables each: Time, X, Y, Boundary Layer '
        'Height Quality Flag, and Footprint Climatology. The flux footprints are computed using FFP as described '
        'in Kljun et al. (2015), https://doi.org/10.5194/gmd-8-3695-2015, at 10-meter spatial resolution using '
        'ETC L2 Fluxes from Romainville, https://hdl.handle.net/11676/TwGCXiTNxEpW-Iq_r8esdE5v. The projection can be customized, but the '
        'footprints were calculated in UTM 32N. This work is part of the ICOS Cities/PAUL Pilot Applications in '
        'Urban Landscapes project.'
    ),
    'zurich': (
        'Daily flux footprints for the Zurich-Hardau flux-tower in Switzerland at 30-minute temporal resolution. '
        'Each dataset contains up to 48 footprints with the following variables each: Time, X, Y, Boundary Layer '
        'Height Quality Flag, and Footprint Climatology. The flux footprints are computed using FFP as described '
        'in Kljun et al. (2015), https://doi.org/10.5194/gmd-8-3695-2015, at 10-meter spatial resolution using '
        'ETC L2 Fluxes from Hardau, https://hdl.handle.net/11676/Lg2RRHAdsLee0lsF-9KsTC-r. The projection can be customized, but the '
        'footprints were calculated in UTM 32N. This work is part of the ICOS Cities/PAUL Pilot Applications in '
        'Urban Landscapes project.'
    ),
}
