BLANKS = {"", "null", "none", "na", "n/a", "-", "nan", "undefined"}

def to_float(value, default=None):
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
     return float(value)
    s = str(value).strip().replace(",", "").replace("%", "")
    if s.lower() in BLANKS:
        return default
    try:
        return float(s)
    except ValueError:
        return default

def to_int(value, default=None):
    f = to_float(value)
    return None if f is None else int(f)