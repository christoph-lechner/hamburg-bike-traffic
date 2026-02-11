def deep_get(d, keys, default_value=None):
    if not isinstance(d,dict):
        return default_value

    # Convenience: user can provide string as argument. It has to be packaged into a single-element list for the following to work
    if isinstance(keys,str):
        keys = [keys]

    for k in keys:
        # print(k)
        # print(d)
        if isinstance(d,dict):
            if not k in d:
                return default_value
            d = d.get(k)
        elif isinstance(d,list):
            try:
                d = d[k]
            except (IndexError,TypeError):
                return default_value
        else:
            # encountered unexpected data type
            return default_value
    return d
