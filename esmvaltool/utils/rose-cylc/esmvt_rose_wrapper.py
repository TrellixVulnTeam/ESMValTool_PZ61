r"""
Install and run u-am444 - the esmvaltool rose-cylc suite.

Usage:
------
-c --config-file:  [REQUIRED]  user specific configuration file;
-r --recipe-file:  [REQUIRED]  single or multiple (space-sep) recipe files;
-d --main-dir:     [OPTIONAL]  main run dir name (full path);
                               defaults to $HOME/ESMVALTOOL_ROSE;
-s --suite-dir     [OPTIONAL]  u-am444 dir full path; can be set by user;
                               defaults to $HOME/u-am444;
-n --no-submit     [OPTIONAL]  if specified, will not submit suite to cylc;
-l --log-level:    [OPTIONAL]  log level, default=info

Example:
--------
python esmvt_rose_wrapper.py -c /home/users/valeriu/input/config-user.yml \
                             -r /home/users/valeriu/recipes/recipe1.yml \
                                /home/users/valeriu/recipes/recipe2.yml \
                             -d /home/users/valeriu/esmvat_WRAPPER \
                             -s /home/users/valeriu/u-am444/ \
                             -n
"""
import argparse
import logging
import os
import sys
import subprocess
import shutil
from distutils.version import LooseVersion
# configparser has changed names in python 3.x
if LooseVersion(sys.version) < LooseVersion("3.0"):
    import ConfigParser
else:
    import configparser as ConfigParser
import yaml  # noqa


# set up logging
logger = logging.getLogger(__name__)

# print the header
HEADER = r"""
______________________________________________________________________

                 ESMValTool Rose-Cylc Wrapper
______________________________________________________________________

""" + __doc__


def get_args():
    """Define the `esmvaltool` command line."""
    # parse command line args
    parser = argparse.ArgumentParser(
        description=HEADER,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '-c',
        '--config-file',
        default=os.path.join(os.path.dirname(__file__), 'config-user.yml'),
        help='Configuration file')
    parser.add_argument(
        '-r',
        '--recipe-files',
        type=str,
        nargs='+',
        help='Recipe files (list or single file)')
    parser.add_argument(
        '-d',
        '--main-dir',
        default=os.path.join(os.environ['HOME'], 'ESMVALTOOL_ROSE'),
        help='Main analysis directory; default to $HOME/ESMVALTOOL_ROSE')
    parser.add_argument(
        '-s',
        '--suite-dir',
        default=os.path.join(os.environ['HOME'], 'u-am444'),
        help='u-am444 suite directory; default to $HOME/u-am444')
    parser.add_argument(
        '-n',
        '--no-submit',
        action='store_true',
        help="Flag to NOT submit the Rose suite.")
    parser.add_argument(
        '-l',
        '--log-level',
        default='info',
        choices=['debug', 'info', 'warning', 'error'])
    args = parser.parse_args()
    return args


def _set_logger(logging, out_dir, log_file, log_level):
    # set logging for screen and file output
    root_logger = logging.getLogger()
    out_fmt = "%(asctime)s %(levelname)-8s %(name)s,%(lineno)s\t%(message)s"
    logging.basicConfig(
        filename=os.path.join(out_dir, log_file),
        filemode='a',
        format=out_fmt,
        datefmt='%H:%M:%S',
        level=logging.DEBUG)
    root_logger.setLevel(log_level.upper())
    logfmt = logging.Formatter(out_fmt)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logfmt)
    root_logger.addHandler(console_handler)


def read_yaml_file(yaml_file):
    """Read recipe into a dictionary."""
    with open(yaml_file, 'r') as yfile:
        loaded_file = yaml.safe_load(yfile)
    return loaded_file


def _setup_work(rose_config_template, recipe_files,
                config_file, main_dir, default_suite, log_level):
    """Write the new rose conf file per suite."""
    # Build the ConfigParser object
    Config = ConfigParser.ConfigParser()
    Config.optionxform = str
    Config.read(rose_config_template)

    # set the main work dir
    if not os.path.exists(main_dir):
        os.makedirs(main_dir)

    # assemble work tree
    if not os.path.isfile(os.path.join(main_dir, config_file)):
        shutil.copy2(config_file, main_dir)
    if not os.path.exists(os.path.join(main_dir, 'recipes')):
        os.makedirs(os.path.join(main_dir, 'recipes'))
    if not os.path.exists(os.path.join(main_dir,
                                       os.path.basename(config_file))):
        shutil.copy2(config_file, main_dir)
    recipes_field = []
    for recipe in recipe_files:
        if not os.path.exists(os.path.join(main_dir, 'recipes',
                                           os.path.basename(recipe))):
            shutil.copy2(recipe, os.path.join(main_dir, 'recipes'))
        recipes_field.append(os.path.basename(recipe).strip('.yml'))
    rose_suite = os.path.join(main_dir, 'u-am444')
    if os.path.exists(rose_suite):
        shutil.rmtree(rose_suite)
    shutil.copytree(default_suite, rose_suite)
    out_dir = os.path.join(main_dir, 'output')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # set logging
    _set_logger(logging, out_dir, 'setup.log', log_level)
    logger.info(HEADER)

    # start logging
    logger.info("Main working directory: %s", main_dir)
    logger.info("Using Rose-Cylc suite base: %s", default_suite)
    logger.info("Output and logs written to: %s", out_dir)
    logger.info("Creating rose suite directories...")
    logger.info("Use rose-suite.conf template %s", rose_config_template)
    logger.info("Use user config file %s", config_file)

    # write the file
    Config.set('jinja2:suite.rc', 'INPUT_DIR',
               '"' + main_dir + '"')
    Config.set('jinja2:suite.rc', 'OUTPUT_DIR', '"' + out_dir + '"')
    Config.set('jinja2:suite.rc', 'RECIPES', str(recipes_field))
    with open(os.path.join(rose_suite, 'rose-suite.conf'), 'w') as r_c:
        logger.info("Writing rose-suite.conf file %s",
                    os.path.join(rose_suite, 'rose-suite.conf'))
        Config.write(r_c)

    return rose_suite


def _run_suite(suite):
    """Run the mip_convert suite."""
    os.chdir(suite)
    logger.info("Submitting suite from %s", suite)
    proc = subprocess.Popen(["rose", "suite-run"], stdout=subprocess.PIPE)
    out, err = proc.communicate()
    logger.info("Rose communications: %s %s", str(out), str(err))


def main():
    """Run the the meat of the code."""
    logger.info("Running main function...")
    args = get_args()
    # rose suite default location
    if args.suite_dir:
        default_suite = args.suite_dir
    rose_config_template = os.path.join(default_suite, "rose-suite.conf")

    # get command line arguments
    recipe_files = args.recipe_files
    config_file = args.config_file
    main_dir = args.main_dir
    log_level = args.log_level

    # setup rose suite
    run_rose = _setup_work(rose_config_template, recipe_files,
                           config_file, main_dir, default_suite, log_level)

    # submit to cylc
    if not args.no_submit:
        _run_suite(run_rose)


if __name__ == '__main__':
    main()
