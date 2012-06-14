import os


__all__ = ['find_files']


def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


def find_packages(package_dir):
    """
    Returns a tuple consisting of a ``packages`` list and a ``package_data``
    dictionary suitable for passing on to ``distutils.core.setup``

    Requires the folder name containing the package files; ``find_files``
    assumes that ``setup.py`` is located in the same folder as the folder
    containing those files.

    Code lifted from Django's ``setup.py``, with improvements by PSyton.
    """

    # Compile the list of packages available, because distutils doesn't have
    # an easy way to do this.
    packages = []
    package_data = {}
    root_dir = os.path.dirname(__file__)
    if root_dir != '':
        os.chdir(root_dir)

    for dirpath, dirnames, filenames in sorted(os.walk(package_dir)):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'): del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(dirpath)))
        elif filenames:
            cur_pack = packages[0] # Assign all data files to the toplevel package
            if cur_pack not in package_data:
                package_data[cur_pack] = []
            package_dir = "/".join(cur_pack.split(".")) + "/"
            for f in filenames:
                package_data[cur_pack].append(os.path.join(dirpath.replace(package_dir, "", 1), f))

    return packages, package_data

