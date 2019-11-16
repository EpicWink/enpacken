"""Package finder."""

import bz2
import lzma
import gzip
import enum
import pathlib
import tarfile
import zipfile
from urllib import request as urllib_request

from wheel import pep425tags


class URL:  # TODO: unit-test, document
    def __init__(self, location):
        self.location = location

    def __truediv__(self, other):
        sep = "" if self.location[-1] == "/" else "/"
        new_location = self.location + sep + other
        return self.__class__(new_location)


class Distribution:  # TODO: unit-test, document
    exts = None

    def __init__(
            self,
            project,
            location,
            version,
            python_implementation,
            python_version,
            abi,
            arch
    ):
        self.project = project
        self.location = location
        self.version = version
        self.python_implementation = python_implementation
        self.python_version = python_version
        self.abi = abi
        self.arch = arch

    @staticmethod
    def _process_filename(filename):
        raise NotImplementedError

    @classmethod
    def from_filename(cls, filename, location, project=None):
        res = cls._process_filename(filename)
        project_norm, version, py_impl, py_version, abi, arch = res
        project = project or project_norm
        return cls(project, location, version, py_impl, py_version, abi, arch)

    @property
    def impl(self):
        return self.python_implementation + self.python_version


class Wheel(Distribution):  # TODO: unit-test, document
    exts = (".whl",)

    @staticmethod
    def _process_filename(filename):
        stem, ext = filename.rsplit(".", maxsplit=1)
        stem_split = stem.split("-")
        project_norm, version, impl, abi, arch = stem_split
        py_impl = impl[:2]
        py_version = impl[2:]
        return project_norm, version, py_impl, py_version, abi, arch


class Source(Distribution):  # TODO: unit-test, document
    exts = (
        ".tar.gz",
        ".zip",
        ".tgz",
        ".tar",
        ".tar.xz",
        ".txz",
        ".tlz",
        ".tar.lz",
        ".tar.lzma",
        ".tar.bz2",
        ".tbz"
    )

    @staticmethod
    def _process_filename(filename):
        stem, ext = filename.rsplit(".", maxsplit=1)
        stem_split = stem.split("-")
        project_norm, version = stem_split
        return project_norm, version, None, None, None, None


DIST_TYPES = [Source, Wheel]


class Index:  # TODO: unit-test, document
    def __init__(self, location):
        self.location = location

    def get_distributions(self, project):
        raise NotImplementedError

    @staticmethod
    def is_this_type(location):
        raise NotImplementedError


class PyPI(Index):  # TODO: unit-test, document
    _pypi_url = URL("https://pypi.org/simple/")

    def __init__(self):
        super().__init__(self._pypi_url)

    def get_distributions(self, project):
        raise NotImplementedError


class Private(PyPI):  # TODO: unit-test, document
    def get_distributions(self, project):
        raise NotImplementedError

    @staticmethod
    def is_this_type(location):
        raise NotImplementedError


class LocalDir(Index):  # TODO: unit-test, document
    def get_distributions(self, project):
        project_norm = project.replace("-", "_")
        location = pathlib.Path(project)
        dists = []
        for path in location.iterdir():
            if not path.resolve().is_file():
                continue
            if path.suffix not in (".whl", ".gz"):
                continue
            if path.suffix == ".gz" and path.stem[-4:] != ".tar":
                continue
            if path.stem[:len(project_norm)] != project_norm:
                continue
            dist_class = get_dist_type(path.name)
            dist = dist_class.from_filename(path.name, path, project=project)
            dists.append(dist)
        return dists

    @staticmethod
    def is_this_type(location):
        try:
            path = pathlib.Path(location)
        except ValueError:
            return False
        path = path.expanduser().resolve()
        path.iterdir()
        return True


INDEX_TYPES = [PyPI, Private, LocalDir]


class DistributionValidator:  # TODO: unit-test, document
    _source_dist_class = Source
    _wheel_dist_class = Wheel

    def __init__(self):
        self.supported = None

    def compute_supported_versions(self):
        self.supported = pep425tags.get_supported()

    def is_valid(self, dist):
        if isinstance(dist, self._source_dist_class):
            return True
        dist_tag = (dist.impl, dist.abi, dist.arch)
        for tag in self.supported:
            if dist_tag == tag:
                return True
        return False


def get_dist_type(dist_filename):  # TODO: unit-test, document
    for dist_type in DIST_TYPES:
        for ext in dist_type.exts:
            if dist_filename[-len(ext):] == ext:
                return dist_type
    raise ValueError("Unsupported distribution type: %s" % dist_filename)


def get_index(index_location):  # TODO: unit-test, document
    for index_type in INDEX_TYPES:
        if index_type.is_this_type(index_location):
            return index_type(index_location)
    raise ValueError("Not an index: %s" % index_location)


def get_indexes(index_locations, pypi=True):  # TODO: unit-test, document
    indexes = []
    for location in index_locations:
        index = get_index(location)
        indexes.append(index)
    if pypi:
        index = PyPI()
        indexes.insert(0, index)
    return indexes


def get_dists(project, indexes):  # TODO: unit-test, document
    dists = []
    for index in indexes:
        dists_index = index.get_distributions(project)
        dists.extend(dists_index)
    return dists


def filter_invalid_candidates(dists):  # TODO: unit-test, document
    validator = DistributionValidator()
    dists_filtered = []
    for dist in dists:
        if validator.is_valid(dist):
            dists_filtered.append(dist)
    return dists_filtered


def get_candidate_score(dist):  # TODO: unit-test, document
    raise NotImplementedError


def sort_candidates(dists):  # TODO: unit-test, document
    return sorted(dists, key=get_candidate_score)


def find_distributions(project, index_locations, pypi=True):  # TODO: unit-test, document
    indexes = get_indexes(index_locations, pypi=pypi)
    dists = get_dists(project, indexes)
    dists = filter_invalid_candidates(dists)
    dists = sort_candidates(dists)
    return dists
