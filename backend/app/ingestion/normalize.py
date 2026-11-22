import re
import unicodedata

_WS = re.compile(r"\s+")


def text(value: object) -> object:
    """NFC-normalise (Vietnamese diacritics have several encodings) and collapse whitespace."""
    if not isinstance(value, str):
        return value
    return _WS.sub(" ", unicodedata.normalize("NFC", value)).strip()


def code(value: object) -> object:
    """Symbols, exchange and currency codes: normalised text, upper-cased, no inner spaces."""
    value = text(value)
    return value.replace(" ", "").upper() if isinstance(value, str) else value


def tax_code(value: object) -> object:
    """Vietnamese tax codes are written with spaces or dots in some documents."""
    value = text(value)
    return re.sub(r"[\s.]", "", value) if isinstance(value, str) else value
