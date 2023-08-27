# Copyright (c) 2023 - 2023, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/.

"""This module tests the Docker build functions."""

from pathlib import Path

import pytest

from macaron.slsa_analyzer.build_tool.docker import Docker
from tests.slsa_analyzer.mock_git_utils import prepare_repo_for_testing


@pytest.mark.parametrize(
    "mock_repo",
    [
        Path(__file__).parent.joinpath("mock_repos", "docker_repos", "root_dockerfile"),
        Path(__file__).parent.joinpath("mock_repos", "docker_repos", "nested_dockerfile"),
        Path(__file__).parent.joinpath("mock_repos", "docker_repos", "root_wildcard_dockerfile"),
        Path(__file__).parent.joinpath("mock_repos", "docker_repos", "root_dockerfile_wildcard"),
        Path(__file__).parent.joinpath("mock_repos", "docker_repos", "no_docker"),
    ],
)
def test_get_build_dirs(snapshot: list, docker_tool: Docker, mock_repo: Path) -> None:
    """Test discovering build directories."""
    assert list(docker_tool.get_build_dirs(str(mock_repo))) == snapshot


@pytest.mark.parametrize(
    ("mock_repo", "expected_value"),
    [
        (Path(__file__).parent.joinpath("mock_repos", "docker_repos", "root_dockerfile"), True),
        (Path(__file__).parent.joinpath("mock_repos", "docker_repos", "nested_dockerfile"), True),
        (Path(__file__).parent.joinpath("mock_repos", "docker_repos", "root_wildcard_dockerfile"), True),
        (Path(__file__).parent.joinpath("mock_repos", "docker_repos", "root_dockerfile_wildcard"), True),
        (Path(__file__).parent.joinpath("mock_repos", "docker_repos", "no_docker"), False),
    ],
)
def test_docker_build_tool(docker_tool: Docker, macaron_path: str, mock_repo: str, expected_value: bool) -> None:
    """Test the Gradle build tool."""
    base_dir = Path(__file__).parent
    ctx = prepare_repo_for_testing(mock_repo, macaron_path, base_dir)
    assert docker_tool.is_detected(ctx.component.repository.fs_path) == expected_value
