# adaption of https://stackoverflow.com/a/43491315
def get_key_or_none(element, *keys):
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            if _element:
                _element = _element[key]
            else:
                return None
        except KeyError:
            return None
    return _element