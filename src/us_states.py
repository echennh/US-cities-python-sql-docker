"""
Lookup helpers for US states.

Supports both → full-name and → abbreviation mappings.
"""
from __future__ import annotations

from typing import Dict


# TODO: read this data in from a file that can be updated without editing code
# Source: US Census Bureau
_ABBREV_TO_NAME = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "PR": "Puerto Rico",
    "GU": "Guam",
    "VI": "U.S. Virgin Islands",
}

_NAME_TO_ABBREV: Dict[str, str] = {v.upper(): k for k, v in _ABBREV_TO_NAME.items()}


def normalize(state_input: str) -> str:
    """
    Convert user input (abbrev or full) to **canonical full state name**.

    Raises:
        KeyError: if the input cannot be resolved.
    """
    state_input = state_input.strip().upper()
    if len(state_input) == 2:  # abbreviation
        return _ABBREV_TO_NAME[state_input]
    return _ABBREV_TO_NAME[_NAME_TO_ABBREV[state_input]]
