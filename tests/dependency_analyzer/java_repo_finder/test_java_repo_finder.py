# Copyright (c) 2023 - 2023, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/.

"""
This module tests the repo finder.
"""
import os
from pathlib import Path

from macaron.config.defaults import defaults
from macaron.dependency_analyzer.java_repo_finder import create_urls, find_parent, find_scm, parse_pom


def test_java_repo_finder() -> None:
    """Test the functions of the repo finder."""
    repositories = defaults.get_list(
        "repofinder.java", "artifact_repositories", fallback=["https://repo.maven.apache.org/maven2"]
    )
    group = "group"
    artifact = "artifact"
    version = "version"
    created_urls = create_urls(group, artifact, version, repositories)
    assert created_urls

    resources_dir = Path(__file__).parent.joinpath("resources")
    with open(os.path.join(resources_dir, "example_pom.xml"), encoding="utf8") as file:
        file_data = file.read()
        pom = parse_pom(file_data)
        assert pom is not None
        found_urls, count = find_scm(
            pom, ["scm.url", "scm.connection", "scm.developerConnection", "licenses.license.distribution"]
        )
        assert count == 4
        expected = [
            "https://github.com/owner/project",
            "ssh://git@hostname:port/owner/Example_License.git",
            "git@github.com:owner/project1.8-2023.git",
            "${licenses.license.distribution}",
        ]
        assert expected == list(found_urls)


def test_java_repo_finder_hierarchical() -> None:
    """Test the hierarchical capabilities of the repo finder."""
    resources_dir = Path(__file__).parent.joinpath("resources")
    with open(os.path.join(resources_dir, "example_pom_no_scm.xml"), encoding="utf8") as file:
        file_data = file.read()
        pom = parse_pom(file_data)
        assert pom is not None
        group, artifact, version = find_parent(pom)
        assert group == "owner"
        assert artifact == "parent"
        assert version == "1"
