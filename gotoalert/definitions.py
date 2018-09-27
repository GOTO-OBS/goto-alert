#! /opt/local/bin/python3.6

import warnings

from astroplan import (AltitudeConstraint, FixedTarget, MoonSeparationConstraint,
                       Observer, is_observable)

import astropy.units as u
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time

import voeventparse as vp


def telescope(name, latitude, longitude, elevation, time_zone):
    """Create an Astroplan observer for the given telescope."""
    location = EarthLocation.from_geodetic(longitude, latitude, elevation * u.m)
    telescope = Observer(name=name, location=location, timezone=time_zone)
    return telescope


def goto_north():
    """Observer for GOTO-North on La Palma."""
    lapalma = EarthLocation.from_geodetic(28.7636, -17.8947, 2396 * u.m)
    telescope = Observer(name='goto_north', location=lapalma, timezone='Atlantic/Canary')
    return telescope


def goto_south():
    """Observer for a (theoretical) GOTO-South in Melbourne."""
    clayton = EarthLocation.from_geodetic(-37.910556, 145.131389, 50 * u.m)
    telescope = Observer(name='goto_south', location=clayton, timezone='Australia/Melbourne')
    return telescope


def event_definitions(v, current_time):
    """Fetch infomation about the event."""

    # Get IVORN
    ivorn = v.attrib['ivorn']

    # Get event time
    event_time = vp.convenience.get_event_time_as_utc(v, index=0)

    # Get event position (RA/DEC)
    pos = vp.get_event_position(v)
    event_coord = SkyCoord(ra=pos.ra, dec=pos.dec, unit=pos.units)
    coorderr = pos.err
    event_str = str(event_coord.ra.value) + ' ' + str(event_coord.dec.value)
    event_target = FixedTarget.from_name(event_str)

    # Get event position (Galactic)
    coord_deg = SkyCoord(event_coord, unit='deg')
    object_galactic_pos = coord_deg.galactic
    object_galactic_lat = coord_deg.galactic.b
    galactic_center = SkyCoord(l=0, b=0, unit='deg,deg', frame='galactic')
    dist_galactic_center = object_galactic_pos.separation(galactic_center)

    data = {'current_time': current_time,
            'event_coord': event_coord,
            'event_coord_error': coorderr,
            'event_target': event_target,
            'event_time': event_time,
            'ivorn': ivorn,
            'object_galactic_lat': object_galactic_lat,
            'dist_galactic_center': dist_galactic_center,
            }
    return data


def observing_definitions(site, target, current_time, alt_limit=30):
    """Compile infomation about the target's visibility from the given site."""
    # Get midnight and astronomicla twilight times
    midnight = site.midnight(current_time, which='next')
    sun_set = site.twilight_evening_astronomical(midnight, which='previous')
    sun_rise = site.twilight_morning_astronomical(midnight, which='next')

    time_range = Time([sun_set, sun_rise])

    # Apply a constraint on altitude
    min_alt = alt_limit * u.deg
    alt_constraint = AltitudeConstraint(min=min_alt, max=None)
    alt_observable = is_observable(alt_constraint, site, target, time_range=time_range)[0]

    # Get target rise and set times
    if alt_observable:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            target_rise = site.target_rise_time(midnight, target, which='nearest', horizon=min_alt)
            target_set = site.target_set_time(target_rise, target, which='next', horizon=min_alt)

        # Get observation times
        observation_start = target_rise
        observation_end = target_set
        if target_rise.jd < 0 or target_set.jd < 0:
            # target is always above the horizon, so visible all night
            observation_start = sun_set
            observation_end = sun_rise
        if target_rise < sun_set:
            # target is already up when the sun sets
            observation_start = sun_set
        if target_set > sun_rise:
            # target sets after the sun rises
            observation_end = sun_rise

    else:
        target_rise = None
        target_set = None
        observation_start = None
        observation_end = None

    # Apply a constraint on distance from the Moon
    min_moon = 5 * u.deg
    moon_constraint = MoonSeparationConstraint(min=min_moon, max=None)
    moon_observable = is_observable(moon_constraint, site, target, time_range=time_range)[0]

    data = {'site': site,
            'midnight': midnight,
            'sun_set': sun_set,
            'sun_rise': sun_rise,
            'target_rise': target_rise,
            'target_set': target_set,
            'observation_start': observation_start,
            'observation_end': observation_end,
            'alt_constraint': alt_constraint,
            'alt_observable': alt_observable,
            'moon_constraint': moon_constraint,
            'moon_observable': moon_observable,
            }

    return data
