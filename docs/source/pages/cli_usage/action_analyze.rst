.. Copyright (c) 2023 - 2023, Oracle and/or its affiliates. All rights reserved.
.. Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/.

.. _analyze-action-cli:

=======
Analyze
=======

-----------
Description
-----------

Analyze a public GitHub repository (and optionally the repositories of its dependencies) to determine its SLSA posture. We currently support `SLSA v0.1 <https://slsa.dev/spec/v0.1/>`_. The support for `SLSA v1.0 <https://slsa.dev/spec/v1.0/>`_ will be added in future.

-----
Usage
-----

.. code-block:: shell

    usage: ./run_macaron.sh analyze
        [-h] [-sbom SBOM_PATH] [-rp REPO_PATH] [-b BRANCH]
        [-d DIGEST] [-pe PROVENANCE_EXPECTATION] [-c CONFIG_PATH]
        [--skip-deps] [-g TEMPLATE_PATH]

-------
Options
-------

.. option:: -h, --help

	Show this help message and exit

.. option:: -sbom SBOM_PATH, --sbom-path SBOM_PATH

    The path to the SBOM of the analysis target.

.. option:: -rp REPO_PATH, --repo-path REPO_PATH

    The path to the repository, can be local or remote


.. option:: -b BRANCH, --branch BRANCH

    The branch of the repository that we want to checkout. If not set, Macaron will use the default branch

.. option:: -d DIGEST, --digest DIGEST

    The digest of the commit we want to checkout in the branch. If not set, Macaron will use the latest commit

.. option:: -pe PROVENANCE_EXPECTATION, --provenance-expectation PROVENANCE_EXPECTATION

    The path to provenance expectation file or directory.

.. option:: -c CONFIG_PATH, --config-path CONFIG_PATH

    The path to the user configuration.

.. option:: --skip-deps

    Skip automatic dependency analysis.

.. option:: -g TEMPLATE_PATH, --template-path TEMPLATE_PATH

    The path to the Jinja2 html template (please make sure to use .html or .j2 extensions).

-----------
Environment
-----------

``GITHUB_TOKEN`` – The GitHub personal access token is needed for to run the analysis. For more information on how to obtain a GitHub token, see instructions in :ref:`Prepare GitHub access token <prepare-github-token>`.
