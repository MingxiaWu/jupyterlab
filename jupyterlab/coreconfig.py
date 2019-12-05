# coding: utf-8
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from collections import defaultdict
from itertools import filterfalse
import json
import os.path as osp

from .jlpmapp import HERE


def pjoin(*args):
    """Join paths to create a real path.
    """
    return osp.abspath(osp.join(*args))


def _get_default_core_data():
    """Get the data for the app template.
    """
    with open(pjoin(HERE, 'staging', 'package.json')) as fid:
        return json.load(fid)


def _is_lab_package(name):
    """Whether a package name is in the lab namespace"""
    return name.startswith('@jupyterlab/')


def _only_nonlab(collection):
    """Filter a dict/sequence to remove all lab packages

    This is useful to take the default values of e.g. singletons and filter
    away the '@jupyterlab/' namespace packages, but leave any others (e.g.
    lumino and react).
    """
    if isinstance(collection, dict):
        return dict(
            (k, v) for (k, v) in collection.items()
            if not _is_lab_package(k)
        )
    elif isinstance(collection, (list, tuple)):
        return list(filterfalse(_is_lab_package, collection))
    raise TypeError('collection arg should be either dict or list/tuple')


class CoreConfig:
    """An object representing a core config.

    This enables custom lab application to override some parts of the core
    configuration of the build system.
    """
    def __init__(self):
        self._data = _get_default_core_data()

    def add(self, name, semver, extension=False, mime_extension=False):
        """Remove an extension/singleton.

        If neither extension or mimeExtension is True (the default)
        the package is added as a singleton dependency.

        name: string
            The npm package name
        semver: string
            The semver range for the package
        extension: bool
            Whether the package is an extension
        mime_extension: bool
            Whether the package is a MIME extension
        """
        data = self._data
        if not name:
            raise ValueError('Missing package name')
        if not semver:
            raise ValueError('Missing package semver')
        if name in data['resolutions']:
            raise ValueError('Package already present: %r' % (name,))
        data['resolutions'][name] = semver

        # If both mimeExtension and extensions are True, treat
        # as mime extension
        if mime_extension:
            data['jupyterlab']['mimeExtensions'][name] = ""
            data['dependencies'][name] = semver
        elif extension:
            data['jupyterlab']['extensions'][name] = ""
            data['dependencies'][name] = semver
        else:
            data['jupyterlab']['singletonPackages'].append(name)

    def remove(self, name):
        """Remove a package/extension.

        name: string
            The npm package name
        """
        data = self._data
        maps = (
            data['dependencies'],
            data['resolutions'],
            data['jupyterlab']['extensions'],
            data['jupyterlab']['mimeExtensions'],
        )
        for m in maps:
            try:
                del m[name]
            except KeyError:
                pass

        data['jupyterlab']['singletonPackages'].remove(name)

    def clear_packages(self, lab_only=True):
        """Clear the packages/extensions.
        """
        data = self._data
        # Clear all dependencies
        if lab_only:
            # Clear all "@jupyterlab/" dependencies
            data['dependencies'] = _only_nonlab(data['dependencies'])
            data['resolutions'] = _only_nonlab(data['resolutions'])
            data['jupyterlab']['extensions'] = _only_nonlab(
                data['jupyterlab']['extensions'])
            data['jupyterlab']['mimeExtensions'] = _only_nonlab(
                data['jupyterlab']['mimeExtensions'])
            data['jupyterlab']['singletonPackages'] = _only_nonlab(
                data['jupyterlab']['singletonPackages'])
        else:
            data['dependencies'] = {}
            data['resolutions'] = {}
            data['jupyterlab']['extensions'] = {}
            data['jupyterlab']['mimeExtensions'] = {}
            data['jupyterlab']['singletonPackages'] = []

    @property
    def extensions(self):
        """A dict mapping all extension names to their semver"""
        data = self._data
        return dict(
            (k, data['resolutions'][k])
            for k in data['jupyterlab']['extensions'].keys())

    @property
    def mime_extensions(self):
        """A dict mapping all MIME extension names to their semver"""
        data = self._data
        return dict(
            (k, data['resolutions'][k])
            for k in data['jupyterlab']['mimeExtensions'].keys())

    @property
    def singletons(self):
        """A dict mapping all singleton names to their semver"""
        data = self._data
        return dict(
            (k, data['resolutions'].get(k, None))
            for k in data['jupyterlab']['singletonPackages'])

    @property
    def static_dir(self):
        return self._data['jupyterlab']['staticDir']

    @static_dir.setter
    def static_dir(self, static_dir):
        self._data['jupyterlab']['staticDir'] = static_dir
