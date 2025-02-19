# Copyright (c) 2022 - 2023, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/.

"""This is the main entrypoint to run Macaron."""

import argparse
import logging
import os
import sys
from importlib import metadata as importlib_metadata

from jinja2 import Environment, FileSystemLoader, select_autoescape
from yamale.schema.validationresults import ValidationResult

import macaron
from macaron.config.defaults import create_defaults, load_defaults
from macaron.config.global_config import global_config
from macaron.config.target_config import TARGET_CONFIG_SCHEMA
from macaron.errors import ConfigurationError
from macaron.output_reporter.reporter import HTMLReporter, JSONReporter, PolicyReporter
from macaron.parsers.yaml.loader import YamlLoader
from macaron.policy_engine.policy_engine import run_policy_engine, show_prelude
from macaron.slsa_analyzer.analyzer import Analyzer
from macaron.slsa_analyzer.git_service import GIT_SERVICES

logger: logging.Logger = logging.getLogger(__name__)


def analyze_slsa_levels_single(analyzer_single_args: argparse.Namespace) -> None:
    """Run the SLSA checks against a single target repository."""
    # Set provenance expectation path.
    if analyzer_single_args.provenance_expectation is not None:
        if not os.path.exists(analyzer_single_args.provenance_expectation):
            logger.critical(
                'The provenance expectation file "%s" does not exist.', analyzer_single_args.provenance_expectation
            )
            sys.exit(os.EX_OSFILE)
        global_config.load_expectation_files(analyzer_single_args.provenance_expectation)

    analyzer = Analyzer(global_config.output_path, global_config.build_log_path)

    # Initiate reporters.
    if analyzer_single_args.template_path:
        custom_jinja_env = Environment(
            loader=FileSystemLoader(os.path.dirname(str(analyzer_single_args.template_path))),
            autoescape=select_autoescape(enabled_extensions=["html", "j2"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        html_reporter = HTMLReporter(
            env=custom_jinja_env, target_template=os.path.basename(analyzer_single_args.template_path)
        )
        if not html_reporter.template:
            logger.error("Exiting because the custom template cannot be found.")
            sys.exit(os.EX_NOINPUT)

        analyzer.reporters.append(html_reporter)
    else:
        analyzer.reporters.append(HTMLReporter())
    analyzer.reporters.append(JSONReporter())

    run_config = {}

    if analyzer_single_args.repo_path:
        # Generate a config dict similar to a config read from user yaml file.
        run_config = {
            "target": {
                "id": analyzer_single_args.repo_path,
                "path": analyzer_single_args.repo_path,
                "branch": analyzer_single_args.branch,
                "digest": analyzer_single_args.digest,
            },
            "dependencies": [],
        }
        validate_result: ValidationResult = TARGET_CONFIG_SCHEMA.validate(run_config, "config_generated", strict=False)
        if not validate_result.isValid():
            logger.critical("The generated config dict is invalid.")
            sys.exit(os.EX_DATAERR)

    elif analyzer_single_args.config_path:
        # Get user config from yaml file
        run_config = YamlLoader.load(analyzer_single_args.config_path)

    status_code = analyzer.run(run_config, analyzer_single_args.sbom_path, analyzer_single_args.skip_deps)
    sys.exit(status_code)


def verify_policy(verify_policy_args: argparse.Namespace) -> int:
    """Run policy engine and verify the Datalog policy.

    Returns
    -------
    int
        Returns os.EX_OK if successful or the corresponding error code on failure.
    """
    if not os.path.isfile(verify_policy_args.database):
        logger.critical("The database file does not exist.")
        return os.EX_OSFILE

    if verify_policy_args.show_prelude:
        show_prelude(verify_policy_args.database)
        return os.EX_OK

    if verify_policy_args.file:
        if not os.path.isfile(verify_policy_args.file):
            logger.critical('The policy file "%s" does not exist.', verify_policy_args.file)
            return os.EX_OSFILE

        result = run_policy_engine(verify_policy_args.database, verify_policy_args.file)
        policy_reporter = PolicyReporter()
        policy_reporter.generate(global_config.output_path, result)

        if ("failed_policies" in result) and any(result["failed_policies"]):
            return os.EX_DATAERR

        return os.EX_OK

    return os.EX_USAGE


def perform_action(action_args: argparse.Namespace) -> None:
    """Perform the indicated action of Macaron."""
    match action_args.action:
        case "dump-defaults":
            # Create the defaults.ini file in the output dir and exit.
            create_defaults(action_args.output_dir, os.getcwd())
            sys.exit(os.EX_OK)

        case "verify-policy":
            sys.exit(verify_policy(action_args))

        case "analyze":
            # Check that the GitHub token is enabled.
            gh_token = os.environ.get("GITHUB_TOKEN")
            if not gh_token:
                logger.error("GitHub access token not set.")
                sys.exit(os.EX_USAGE)
            global_config.gh_token = gh_token

            # TODO: Here we should try to statically analyze the config before
            # actually running the analysis.
            try:
                for git_service in GIT_SERVICES:
                    git_service.load_defaults()
            except ConfigurationError as error:
                logger.error(error)
                sys.exit(os.EX_USAGE)

            analyze_slsa_levels_single(action_args)
        case _:
            logger.error("Macaron does not support command option %s.", action_args.action)
            sys.exit(os.EX_USAGE)


def main(argv: list[str] | None = None) -> None:
    """Execute Macaron as a standalone command-line tool.

    Parameters
    ----------
    argv: list[str] | None
        Command-line arguments.
        If ``argv`` is ``None``, argparse automatically looks at ``sys.argv``.
        Hence, we set ``argv = None`` by default.
    """
    main_parser = argparse.ArgumentParser(prog="macaron")

    main_parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {importlib_metadata.version('macaron')}",
        help="Show Macaron's version number and exit",
    )

    main_parser.add_argument(
        "-v",
        "--verbose",
        help="Run Macaron with more debug logs",
        action="store_true",
    )

    main_parser.add_argument(
        "-o",
        "--output-dir",
        default=os.path.join(os.getcwd(), "output"),
        help="The output destination path for Macaron",
    )

    main_parser.add_argument(
        "-dp",
        "--defaults-path",
        default="",
        help="The path to the defaults configuration file.",
    )

    main_parser.add_argument(
        "-lr",
        "--local-repos-path",
        default="",
        help="The directory where Macaron looks for already cloned repositories.",
    )

    # Add sub parsers for each action
    sub_parser = main_parser.add_subparsers(dest="action", help="Run macaron <action> --help for help")

    # Use Macaron to analyze one single repository.
    single_analyze_parser = sub_parser.add_parser(name="analyze")
    group = single_analyze_parser.add_mutually_exclusive_group(required=True)

    single_analyze_parser.add_argument(
        "-sbom",
        "--sbom-path",
        required=False,
        type=str,
        default="",
        help=("The path to the SBOM of the analysis target."),
    )

    group.add_argument(
        "-rp",
        "--repo-path",
        required=False,
        type=str,
        help=("The path to the repository, can be local or remote"),
    )

    single_analyze_parser.add_argument(
        "-b",
        "--branch",
        required=False,
        type=str,
        default="",
        help=("The branch of the repository that we want to checkout. If not set, Macaron will use the default branch"),
    )

    single_analyze_parser.add_argument(
        "-d",
        "--digest",
        required=False,
        type=str,
        default="",
        help=(
            "The digest of the commit we want to checkout in the branch. "
            + "If not set, Macaron will use the latest commit"
        ),
    )

    single_analyze_parser.add_argument(
        "-pe",
        "--provenance-expectation",
        required=False,
        help=("The path to provenance expectation file or directory."),
    )

    group.add_argument(
        "-c",
        "--config-path",
        required=False,
        type=str,
        default="",
        help=("The path to the user configuration."),
    )

    single_analyze_parser.add_argument(
        "--skip-deps",
        required=False,
        action="store_true",
        default=False,
        help=("Skip automatic dependency analysis."),
    )

    single_analyze_parser.add_argument(
        "-g",
        "--template-path",
        required=False,
        type=str,
        default="",
        help=("The path to the Jinja2 html template (please make sure to use .html or .j2 extensions)."),
    )

    # Dump the default values.
    sub_parser.add_parser(name="dump-defaults", description="Dumps the defaults.ini file to the output directory.")

    # Verify the Datalog policy.
    vp_parser = sub_parser.add_parser(name="verify-policy")
    vp_group = vp_parser.add_mutually_exclusive_group(required=True)

    vp_parser.add_argument("-d", "--database", required=True, type=str, help="Path to the database.")
    vp_group.add_argument("-f", "--file", type=str, help="Path to the Datalog policy.")
    vp_group.add_argument("-s", "--show-prelude", action="store_true", help="Show policy prelude.")

    args = main_parser.parse_args(argv)

    if not args.action:
        main_parser.print_help()
        sys.exit(os.EX_USAGE)

    if args.verbose:
        log_level = logging.DEBUG
        log_format = "%(asctime)s [%(name)s:%(funcName)s:%(lineno)d] [%(levelname)s] %(message)s"
    else:
        log_level = logging.INFO
        log_format = "%(asctime)s [%(levelname)s] %(message)s"

    # Set global logging config. We need the stream handler for the initial
    # output directory checking log messages.
    st_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(format=log_format, handlers=[st_handler], force=True, level=log_level)

    # Set the output directory.
    if not args.output_dir:
        logger.error("The output path cannot be empty. Exiting ...")
        sys.exit(os.EX_USAGE)

    if os.path.isfile(args.output_dir):
        logger.error("The output directory already exists. Exiting ...")
        sys.exit(os.EX_USAGE)

    if os.path.isdir(args.output_dir):
        logger.info("Setting the output directory to %s", args.output_dir)
    else:
        logger.info("No directory at %s. Creating one ...", args.output_dir)
        os.makedirs(args.output_dir)

    # Add file handler to the root logger. Remove stream handler from the
    # root logger to prevent dependencies printing logs to stdout.
    debug_log_path = os.path.join(args.output_dir, "debug.log")
    log_file_handler = logging.FileHandler(debug_log_path, "w")
    log_file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().removeHandler(st_handler)
    logging.getLogger().addHandler(log_file_handler)

    # Add StreamHandler to the Macaron logger only.
    mcn_logger = logging.getLogger("macaron")
    mcn_logger.addHandler(st_handler)

    logger.info("The logs will be stored in debug.log")

    # Set Macaron's global configuration.
    # The path to provenance expectation files will be updated if
    # set through analyze sub-command.
    global_config.load(
        macaron_path=macaron.MACARON_PATH,
        output_path=args.output_dir,
        build_log_path=os.path.join(args.output_dir, "build_log"),
        debug_level=log_level,
        local_repos_path=args.local_repos_path,
        resources_path=os.path.join(macaron.MACARON_PATH, "resources"),
    )

    # Load the default values from defaults.ini files.
    if not load_defaults(args.defaults_path):
        logger.error("Exiting because the defaults configuration could not be loaded.")
        sys.exit(os.EX_NOINPUT)

    perform_action(args)


if __name__ == "__main__":
    main()
