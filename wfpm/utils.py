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
import subprocess
from glob import glob
from click import echo


def locate_nearest_parent_dir_with_file(start_dir=None, filename=None):
    paths = os.path.abspath(start_dir).split(os.path.sep)

    for i in sorted(range(len(paths)), reverse=True):
        path = os.path.sep.join(paths[:(i+1)])
        if os.path.isfile(os.path.join(path, filename)):
            return path


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def run_cmd(cmd):
    # keep this simple for now
    proc = subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
    stdout, stderr = proc.communicate()

    return (
        stdout.decode("utf-8").strip(),
        stderr.decode("utf-8").strip(),
        proc.returncode
    )


def test_package(pkg_path):
    test_path = os.path.join(pkg_path, 'tests')
    job_files = sorted(glob(os.path.join(test_path, 'test-*.json')))
    test_count = len(job_files)
    failed_count = 0
    for i in range(test_count):
        cmd = f"cd {test_path} && ./checker.nf -params-file {job_files[i]}"
        echo(f"[{i+1}/{test_count}] Testing: {job_files[i]}. ", nl=False)
        out, err, ret = run_cmd(cmd)
        if ret != 0:
            failed_count += 1
            echo(f"FAILED")
            echo(f"STDOUT: {out}")
            echo(f"STDERR: {err}")
        else:
            echo(f"PASSED")

    if not test_count:
        echo(f"No test to run.")

    echo(f"Tested package: {os.path.basename(pkg_path)}, PASSED: {test_count - failed_count}, FAILED: {failed_count}")

    return failed_count  # return number of failed tests
