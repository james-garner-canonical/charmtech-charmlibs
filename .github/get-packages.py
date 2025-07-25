# Copyright 2024 Canonical Ltd.
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

"""Output changed packages, or all packages if global config files have changed.

Assumes that the current working directory is the project root.
The git reference to diff with must be provided as a commandline argument.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess

_GLOBAL_FILES = ('.github', 'justfile', 'pyproject.toml')


def _parse_args() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument('git_base_ref', nargs='?', default='')
    args = parser.parse_args()
    return args.git_base_ref


def _main(git_base_ref: str) -> None:
    packages = _get_changed_packages(git_base_ref=git_base_ref)
    line = f'packages={json.dumps(packages)}'
    print(line)
    with pathlib.Path(os.environ['GITHUB_OUTPUT']).open('a') as f:
        print(line, file=f)


def _get_changed_packages(git_base_ref: str) -> list[str]:
    paths = [pathlib.Path('_charmlibs'), *pathlib.Path().glob(r'[a-z]*')]
    all_packages = sorted(path.name for path in paths if path.is_dir())
    if not git_base_ref:
        print('Using all packages because no git base ref was provided:')
        return all_packages
    cmd = ['git', 'diff', '--name-only', f'origin/{git_base_ref}']
    diff = subprocess.check_output(cmd, text=True)
    changes = {path.split('/')[0] for path in diff.split('\n')}
    if global_changes := sorted(changes.intersection(_GLOBAL_FILES)):
        print(f'Using all packages because global files were changed: {global_changes}')
        return all_packages
    print(f'Using packages that are changed compared to {git_base_ref}:')
    return sorted(changes.intersection(all_packages))


if __name__ == '__main__':
    _main(git_base_ref=_parse_args())
