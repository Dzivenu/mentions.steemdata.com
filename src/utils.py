import re


# url parsing
# -----------
def resolve_identifier(identifier):
    match = re.match("@?([\w\-\.]*)/([\w\-]*)", identifier)
    if not hasattr(match, "group"):
        raise ValueError("Invalid identifier")
    return match.group(1), match.group(2)


def extract_identifier(uri):
    return '@%s' % uri.split('@')[-1]


def parse_identifier(uri_or_identifier):
    try:
        return resolve_identifier(extract_identifier(uri_or_identifier))
    except (TypeError, ValueError):
        pass
