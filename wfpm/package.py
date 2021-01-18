# -*- coding: utf-8 -*-

"""
    Copyright (c) 2021, Ontario Institute for Cancer Research (OICR).

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    Authors:
        Junjun Zhang <junjun.zhang@oicr.on.ca>
"""

import os
import re
import requests
import tempfile
from wfpm import PKG_NAME_REGEX, PKG_VER_REGEX
from .project import Project
from .utils import run_cmd


class Package(object):
    def __init__(self, pkg_uri=None, pkg_json=None):
        if pkg_uri and pkg_json:
            raise Exception("Cannot specify both pkg_uri and pkg_json")
        elif pkg_uri:
            self._init_by_uri(pkg_uri)
        elif pkg_json:
            self._init_by_json(pkg_json)
        else:
            raise Exception("Must specify either pkg_uri or pkg_json")

        self.pkg_uri = f"{self.project.fullname}/{self.fullname}"
        pkg_tar = self.fullname.replace('@', '.')
        self.download_url = f"https://{self.project.fullname}/releases/download/{pkg_tar}/{pkg_tar}.tar.gz"

    def _init_by_uri(self, pkg_uri):
        try:
            repo_server, repo_account, repo_name, pkg_fullname = pkg_uri.split('/')
            name, version = pkg_fullname.split('@')
        except ValueError:
            raise Exception(f"Invalid package uri: {pkg_uri}, expected format: "
                            "repo_server/repo_account/repo_name/pkg_name@pkg_version")

        if not re.match(PKG_NAME_REGEX, name):
            raise Exception(f"Invalid package name: {name}, expected name pattern: {PKG_NAME_REGEX}")

        if not re.match(PKG_VER_REGEX, version):
            raise Exception(f"Invalid package version: {version}, expected version pattern: {PKG_VER_REGEX}")

        # create Project object
        self.project = Project(
            repo_type='git',  # hardcode for now
            repo_server=repo_server,
            repo_account=repo_account,
            repo_name=repo_name
        )

        self.fullname = pkg_fullname
        self.name = name
        self.version = version

    def _init_by_json(self, json):
        pass

    def install(self, target_project_root, include_tests=False, force=False):
        target_path = os.path.join(
            target_project_root,
            'wfpr_modules',
            self.project.repo_server,
            self.project.repo_account,
            self.project.name,
            self.fullname
        )

        if os.path.isdir(target_path) and not force:
            raise Exception(f"Pakcage already installed: {target_path}, skip unless force option is specified.")

        if force:
            out, err, ret = run_cmd(f"rm -fr {target_path}")  # remove possible previous installation
            if ret != 0:
                raise Exception(f"Unable to remove previously installed package: {err}")

        response = requests.get(self.download_url, stream=True)
        if response.status_code == 200:
            with tempfile.TemporaryDirectory() as tmpdirname:
                local_tar_path = os.path.join(tmpdirname, os.path.basename(self.download_url))

                with open(local_tar_path, 'wb') as f:
                    for chunk in response.raw.stream(1024, decode_content=False):
                        if chunk:
                            f.write(chunk)

                arg_exclude = "" if include_tests else "--exclude='tests'"
                cmd = f"mkdir -p {target_path} && " \
                      f"tar -xzf {local_tar_path} {arg_exclude} -C {target_path} && " \
                      f"cd {target_path} && ln -s ../../../../../wfpr_modules . "
                if include_tests:
                    cmd += "&& cd tests && ln -s ../wfpr_modules ."

                out, err, ret = run_cmd(cmd)
                if ret != 0:
                    run_cmd(f"rm -fr {target_path}")  # undo partial installation
                    raise Exception(f"Package downloaded but installation failed: {err}")

                return target_path  # return the path the package was installed

        else:
            raise Exception(f"Looks like this package has not been released: {self.pkg_uri}")

    def __repr__(self):
        return self.pkg_uri