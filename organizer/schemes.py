"""Standard knowledge-classification codes for the built-in categories.

Each built-in category is annotated with:
  - its Library of Congress Classification (LCC) top class (public domain,
    https://www.loc.gov/catdir/cpso/lcc.html)
  - its arXiv subject area (open taxonomy, https://arxiv.org/category_taxonomy)

These codes are purely informational: they appear in the reports and in
`--list-categories` so users can relate the tool's folders to standards used by
libraries and preprint servers. They never affect classification or file moves.

Personal/practical documents (bills, certificates, bookings, ...) have no class
in any library or scientific scheme; their LCC code is empty by design.
"""

LCC_TOP = {
    "B": "B - Philosophy. Psychology. Religion",
    "H": "H - Social Sciences",
    "K": "K - Law",
    "L": "L - Education",
    "M": "M - Music",
    "P": "P - Language and Literature",
    "Q": "Q - Science",
    "R": "R - Medicine",
    "T": "T - Technology",
}

# category -> LCC top-class letter ('' = personal/practical document, no class)
LCC_MAP = {
    # audio & speech engineering
    "noise_reduction": "T", "echo_cancellation": "T", "adaptive_filtering": "T",
    "beamforming": "T", "spatial_audio": "T", "room_acoustics": "T",
    "loudspeakers": "T", "microphones_transducers": "T", "audio_coding": "T",
    "audio_measurement": "T", "audio_production_broadcast": "T",
    "audio_converters_interfaces": "T", "audio_effects_reverb": "T",
    "audio_equalization": "T", "audio_general": "T",
    "speech_recognition": "T", "speech_synthesis": "T", "speech_analysis": "T",
    # math / DSP
    "machine_learning": "Q", "statistics_probability": "Q", "optimization": "Q",
    "mathematics_reference": "Q", "dsp_general": "T", "filter_design": "T",
    "estimation_tracking": "T",
    # computing
    "programming_python": "Q", "programming_cpp": "Q", "programming_java": "Q",
    "programming_other": "Q", "software_engineering": "Q", "operating_systems": "Q",
    "networking": "T", "databases": "Q", "web_dev": "Q", "embedded": "T",
    "rf_microwave": "T", "circuits": "T", "video_image": "T",
    # other
    "hearing_aids_audiology": "R", "music_audio": "M",
    "finance_accounting": "H", "bank_tax": "H", "career_interview": "H",
    "contracts_agreements": "K", "danish_education": "L", "self_help": "B",
    "writing_media": "P", "fiction": "P", "misc_reading": "P",
    "product_manuals": "T",
    # personal/practical documents: no standard class
    "travel_bookings": "", "certificates_ids": "", "insurance_pension": "",
    "bills_utilities": "", "misc_admin": "",
}

# category -> arXiv subject area ('' = no matching arXiv area)
ARXIV_MAP = {
    "noise_reduction": "eess.AS", "echo_cancellation": "eess.AS",
    "adaptive_filtering": "eess.SP", "beamforming": "eess.AS",
    "spatial_audio": "eess.AS", "room_acoustics": "eess.AS",
    "loudspeakers": "eess.AS", "microphones_transducers": "eess.AS",
    "audio_coding": "eess.AS", "audio_measurement": "eess.AS",
    "audio_production_broadcast": "eess.AS",
    "audio_converters_interfaces": "eess.AS", "audio_effects_reverb": "eess.AS",
    "audio_equalization": "eess.AS", "audio_general": "cs.SD",
    "speech_recognition": "eess.AS", "speech_synthesis": "eess.AS",
    "speech_analysis": "eess.AS", "hearing_aids_audiology": "eess.AS",
    "music_audio": "cs.SD",
    "dsp_general": "eess.SP", "filter_design": "eess.SP",
    "estimation_tracking": "eess.SP", "rf_microwave": "eess.SP",
    "machine_learning": "cs.LG", "statistics_probability": "math.PR",
    "optimization": "math.OC", "mathematics_reference": "math.GM",
    "programming_python": "cs.PL", "programming_cpp": "cs.PL",
    "programming_java": "cs.PL", "programming_other": "cs.PL",
    "software_engineering": "cs.SE", "operating_systems": "cs.OS",
    "networking": "cs.NI", "databases": "cs.DB", "web_dev": "cs.SE",
    "embedded": "cs.AR", "circuits": "cs.AR", "video_image": "cs.CV",
    "finance_accounting": "q-fin",
}


def standard_codes(cat):
    """Return (lcc_top_class, arxiv_area) for a category ('' when unmapped)."""
    return LCC_MAP.get(cat, ""), ARXIV_MAP.get(cat, "")


def lcc_label(cat):
    """Human-readable LCC top class, e.g. 'T - Technology' ('' when unmapped)."""
    letter = LCC_MAP.get(cat, "")
    return LCC_TOP.get(letter, "") if letter else ""
