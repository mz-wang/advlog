# Copyright 2026 Mengzhao Wang
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for log file naming."""

from pathlib import Path

from advlog import LogNamingStrategy


class TestIncremental:
    def test_creates_missing_directory(self, tmp_path):
        """The target directory itself is created, not just its parent."""
        directory = tmp_path / "new" / "dir"
        path = LogNamingStrategy.incremental("app", directory=directory)
        assert directory.is_dir()
        assert Path(path) == directory / "app.log"

    def test_numbers_existing_files(self, tmp_path):
        """An existing file gets a numbered successor instead of being reused."""
        (tmp_path / "app.log").touch()
        (tmp_path / "app_1.log").touch()
        assert Path(LogNamingStrategy.incremental("app", directory=tmp_path)) == tmp_path / "app_2.log"
