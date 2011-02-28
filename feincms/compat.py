def c_any(iterable):
    """
    Implements python 2.5's any()
    """

    for element in iterable:
        if element:
            return True
    return False

def c_all(iterable):
    """
    Implements python 2.5's all()
    """

    for element in iterable:
        if not element:
            return False
    return True
