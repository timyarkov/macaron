# Copyright (c) 2022 - 2023, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/.

"""This module processes the JSON dependency output files generated by CycloneDX Maven plugin.

It also collects the direct dependencies that should be processed by Macaron.
See https://github.com/CycloneDX/cyclonedx-maven-plugin.
"""

import glob
import logging
import os
from pathlib import Path

from macaron.config.defaults import defaults
from macaron.dependency_analyzer import DependencyAnalyzer
from macaron.dependency_analyzer.cyclonedx import (
    convert_components_to_artifacts,
    get_dep_components,
    get_root_component,
)
from macaron.dependency_analyzer.dependency_resolver import DependencyInfo

logger: logging.Logger = logging.getLogger(__name__)


class CycloneDxMaven(DependencyAnalyzer):
    """This class implements the CycloneDX Maven plugin analyzer."""

    def get_cmd(self) -> list:
        """Return the CLI command to run the CycloneDX Maven plugin.

        Returns
        -------
        list
            The command line arguments.
        """
        logger.info(
            (
                "The SBOM generator has started resolving the dependencies and storing them in %s files. "
                "This might take a while..."
            ),
            self.file_name,
        )
        return [
            os.path.join(self.resources_path, "mvnw"),
            f"org.cyclonedx:cyclonedx-maven-plugin:{self.tool_version}:makeAggregateBom",
            "-D",
            "includeTestScope=true",
        ]

    def collect_dependencies(self, dir_path: str) -> dict[str, DependencyInfo]:
        """Process the dependency JSON files and collect direct dependencies.

        Parameters
        ----------
        dir_path : str
            Local path to the target repo.

        Returns
        -------
        dict
            A dictionary where artifacts are grouped based on "artifactId:groupId".
        """
        # Load the top level file separately as it has different content.
        top_path = Path(os.path.join(dir_path, "target", self.file_name))

        # Collect all the dependency files recursively.
        child_paths = [
            Path(path)
            for path in glob.glob(os.path.join(dir_path, "**", "target", self.file_name), recursive=True)
            if Path(path) != top_path
        ]

        # Check if the root BOM has been analyzed before as a child BOM.
        self.visited_deps.update(child_paths)
        if top_path in self.visited_deps:
            return {}

        root_component = get_root_component(top_path)
        components = get_dep_components(
            top_path,
            child_paths,
            recursive=defaults.getboolean(
                "dependency.resolver",
                "recursive",
                fallback=False,
            ),
        )
        return convert_components_to_artifacts(components, root_component)

    def remove_sboms(self, dir_path: str) -> bool:
        """Remove all the SBOM files in the provided directory recursively.

        Parameters
        ----------
        dir_path : str
            Path to the repo.

        Returns
        -------
        bool
            Returns True if all the files are removed successfully.
        """
        removed_all = True
        for path in glob.glob(os.path.join(dir_path, "**", "target", self.file_name), recursive=True):
            try:
                os.remove(path=path)
                logger.debug("Successfully removed %s.", path)
            except OSError as error:
                logger.error(error)
                removed_all = False

        return removed_all
