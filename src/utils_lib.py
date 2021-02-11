"""Module containing utility functions general use."""
# import ast
import json
import os # TODO replace all os.path operations with pathlib equivalents
import pathlib

import src.config.config as cnf
import src.config.templates as templates


MSG = cnf.MSG
EXAMPLES = cnf.EXAMPLES
TITLE_TO_EXAMPLES = cnf.TITLE_TO_EXAMPLES

IGNORE = cnf.IGNORE
GENERAL = cnf.GENERAL
ERROR = cnf.ERROR
WARNING = cnf.WARNING
NOTE = cnf.NOTE
GOOD = cnf.GOOD
DEBUG = cnf.DEBUG


# General utilities

def ignore_check(code):
    if code in IGNORE:
        return True
    else:
        return False


def create_msg(code, *args, lineno=-1, lang="FIN"):
    """
    Function to create violation message based on given violation code,
    message parameters (e.g. variable name), linenumber and language.

    Return:
    1. msg - violation message - string
    2. severity - severity level of message - integer number
        (numbers are predefined global constants)
    3. start - character index of violation message's start position
        - integer number
    4. end - character index of violation message's end position
        - integer number
    """
    msg = ""
    start = 0
    end = 0
    severity = MSG[lang]["default"][1]
    # if lineno < 0:
    #     pass
    if lineno >= 0 and lang:
        msg = f"{MSG[lang]['LINE'][0]} {lineno}: "
        start = len(msg)

    try:
        msg += MSG[lang][code][0]
        severity = MSG[lang][code][1]
    except KeyError:
        msg += MSG[lang]["default"][0]
    else:
        try:
            msg = msg.format(*args)
        except IndexError:
            msg = MSG[lang]["error_error"][0]
    finally:
        end = len(msg)

    return msg, severity, start, end


def get_title(title_key, lang):
    try:
        return cnf.TEXT[lang][title_key]
    except KeyError:
        return None


def create_title(code, title_key, lang="FIN"):
    title = get_title(title_key, lang)
    msg = ""
    start = 0
    end = 0
    severity = GENERAL
    if title:
        msg = title
        start = len(msg) + 1

    try:
        if title_key != "analysis_error":
            msg += MSG[lang][code][0]
            severity = MSG[lang][code][1]

            if code == "NOTE":
                exs = TITLE_TO_EXAMPLES[title_key]
                for i in exs:
                    if i == "EX0":
                        msg += f" {EXAMPLES[i]}"
                    else:
                        msg += f" '{EXAMPLES[i]}'"
                msg += ":"
    except KeyError:
        pass

    finally:
        end = len(msg)

    return msg, severity, start, end


def crawl_dirs(paths, only_leaf_files=False):
    filelist = []
    for path in paths:
        if os.path.isdir(path):
            for current_dir, dirs, all_files in os.walk(path):
                if not all_files or (only_leaf_files and dirs):
                    continue
                files = [f for f in all_files if(f.endswith(".py"))]

                for f in files:
                    filelist.append(os.path.join(current_dir, f))
        elif os.path.isfile(path) and path.endswith(".py"):
            filelist.append(path)
        # else # file is a special file e.g. socket, FIFO or device file
        # OR not .py file.
    return filelist

def crawl_files_to_dict(paths, excluded_dirs, excluded_files=(), only_leaf_files=True, *args, **kwargs):
    """
    Function to crawl all (sub)directories and return filepaths based on
    given rules.
    """
    def remove_excluded(dirs, excluded):
        for e in excluded:
            try:
                dirs.remove(e)
            except ValueError:
                pass

    def add_file(file_d, filepath):
        student = 0
        exercise = 1
        week = 2 # exam
        # course = 3

        student_str = filepath.parents[student].name
        week_str = filepath.parents[week].name
        exercise_str = filepath.parents[exercise].name

        file_d.setdefault(student_str, []).append(templates.FilepathTemplate(
            path=filepath,
            student=student_str,
            week=week_str,
            exercise=exercise_str
        ))

    file_dict = {}
    for path_str in paths:
        path_obj = pathlib.Path(path_str).resolve()
        if path_obj.is_dir():
            # for sub in path_obj.glob("**/*.py"): # NOTE glob itself does not
            # allow selecting only leaf files, therefore os.path.walk is used.
            for current_dir, dirs, all_files in os.walk(path_obj, topdown=True):
                remove_excluded(dirs, excluded_dirs)

                if not all_files or (only_leaf_files and dirs):
                    continue

                for f in all_files:
                    if f.endswith(".py") and not f in excluded_files:
                        add_file(file_dict, pathlib.Path(current_dir).joinpath(f))

        elif path_obj.is_file() and path_obj.suffix == ".py":
            add_file(file_dict, path_obj)

    return file_dict


def read_file(filepath, encoding="UTF-8", settings_file=False):
    content = None
    try:
        with open(filepath, "r", encoding=encoding) as f_handle:
            content = f_handle.read() # Add pass / fail metadata extraction
    except OSError:
        if not settings_file:
            print("OSError while reading a file", filepath)
    except:
        pass
    return content


def write_file(filepath, content, mode="w", encoding="UTF-8", repeat=True):
    try:
        with open(filepath, mode=mode, encoding=encoding) as f_handle:
            f_handle.write(content)

    except FileNotFoundError: # When subdirectory is not found
        try:
            path = pathlib.Path(filepath)
            path.parent.absolute().mkdir(parents=True, exist_ok=True)
            if repeat:
                # This call is first level recursion
                write_file(
                    filepath,
                    content,
                    mode=mode,
                    encoding=encoding,
                    repeat=False # To prevent infinite repeat loop
                )
        except OSError:
            print("OSError while writing a file", filepath)
    except OSError:
        print("OSError while writing a file", filepath)
    except Exception:
        print("Other error than OSError with file", filepath)
    return None


def print_title(title):
    print(f"--- {title} ---")


def create_dash(character="-", dash_count=80, get_dash=False):
    if get_dash:
        return character * dash_count
    else:
        print(character * dash_count)


# INIT FUNCTIONS
def add_fixed_settings(settings):
    # Checkbox options
    settings["checkbox_options"] = cnf.CHECKBOX_OPTIONS

    # Result file paths
    result_dir = pathlib.Path(settings["result_dir"])
    settings["result_path"] = result_dir.joinpath(settings["result_file"])
    settings["BKT_path"] = result_dir.joinpath(settings["BKT_file"])

def init_settings():
    settings = cnf.DEFAULT_SETTINGS # Currently reference not copy
    settings_file = settings["settings_file"]

    content = read_file(settings_file, settings_file=True)
    if content:
        for key, value in json.loads(content).items():
            settings[key] = value
    else:
        content = json.dumps(settings, indent=4)
        write_file(settings_file, content, mode="w")
    add_fixed_settings(settings)
    return settings
