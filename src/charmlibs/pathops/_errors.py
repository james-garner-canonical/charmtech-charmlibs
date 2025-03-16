# Copyright 2025 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Methods for matching Python Exceptions to Pebble Errors and creating Exception objects."""

from __future__ import annotations

import errno
import os
from typing import NoReturn

from ops import pebble


def raise_file_exists(msg: str, from_: BaseException | None = None) -> NoReturn:
    raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), msg) from from_


def raise_if_matches_file_exists(error: pebble.Error, msg: str) -> None:
    if (
        isinstance(error, pebble.PathError)
        and error.kind == 'generic-file-error'
        and 'file exists' in error.message
    ):
        raise_file_exists(msg, from_=error)


def raise_file_not_found(msg: str, from_: BaseException | None = None) -> NoReturn:
    # pebble will return this error when trying to read_{text,bytes} a socket
    # pathlib raises OSError(errno.ENXIO, os.strerror(errno.ENXIO), path) in this case
    # displaying as "OSError: [Errno 6] No such device or address: '/path'"
    # since FileNotFoundError is a subtype of OSError, and this case should be rare
    # it seems sensible to just raise FileNotFoundError here, without checking
    # if the file in question is a socket
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), msg) from from_


def raise_if_matches_file_not_found(error: pebble.Error, msg: str) -> None:
    if (isinstance(error, pebble.APIError) and error.code == 404) or (
        isinstance(error, pebble.PathError) and error.kind == 'not-found'
    ):
        raise_file_not_found(msg, from_=error)


def raise_if_matches_is_a_directory(error: pebble.Error, msg: str) -> None:
    if (
        isinstance(error, pebble.PathError)
        and error.kind == 'generic-file-error'
        and 'can only read a regular file' in error.message
    ):
        raise IsADirectoryError(errno.EISDIR, os.strerror(errno.EISDIR), msg) from error


def raise_if_matches_lookup(error: pebble.Error, msg: str) -> None:
    if (
        isinstance(error, pebble.PathError)
        and error.kind == 'generic-file-error'
        and 'cannot look up user and group' in error.message
    ):
        raise LookupError(msg) from error


def matches_not_a_directory(error: pebble.Error) -> bool:
    return (
        isinstance(error, pebble.PathError)
        and error.kind == 'generic-file-error'
        and 'not a directory' in error.message
    )


def raise_not_a_directory(msg: str, from_: BaseException | None = None) -> NoReturn:
    raise NotADirectoryError(errno.ENOTDIR, os.strerror(errno.ENOTDIR), msg) from from_


class Permission:
    @staticmethod
    def matches(error: pebble.Error) -> bool:
        return isinstance(error, pebble.PathError) and error.kind == 'permission-denied'

    @staticmethod
    def exception(msg: str) -> PermissionError:
        return PermissionError(errno.EPERM, os.strerror(errno.EPERM), msg)


class TooManyLevelsOfSymbolicLinks:
    @staticmethod
    def matches(error: pebble.Error) -> bool:
        return (
            isinstance(error, pebble.APIError)
            and error.code == 400
            and 'too many levels of symbolic links' in error.message
        )

    @classmethod
    def exception(cls, msg: str) -> OSError:
        return OSError(errno.ELOOP, os.strerror(errno.ELOOP), msg)

    @staticmethod
    def matches_exception(exception: Exception) -> bool:
        return isinstance(exception, OSError) and exception.errno == errno.ELOOP
