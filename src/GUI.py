"""GUI controller"""

try:
    import Tkinter as tk  # Python 2
except ModuleNotFoundError:
    import tkinter as tk  # Python 3, tested with this
    from tkinter import ttk

import datetime  # for timestamp
import os

import src.analysers.analysis_lib as analysis  # Model
import src.config.config as cnf
import src.utils_lib as utils
import src.view_lib as view  # View

# Constants
TOOL_NAME = cnf.TOOL_NAME


class GUICLASS(tk.Tk):
    """Main class for GUI. Master for every used GUI element. The main
    frame and menubar are inlcuded in the here other GUI elements are
    in view. Works as a MVP model presenter/ MVC model controller.
    """

    def __init__(self, *args, settings={}, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # tk.Tk.iconbitmap(self, default="icon.ico")  # To change logo icon
        tk.Tk.title(self, TOOL_NAME)

        self.settings = settings
        self.LANG = settings["language"]
        self.model = analysis.Model(self)
        self.cli = view.CLI(self.LANG)

        self.main_frame = view.MainFrame(self, self.LANG)

        # Display the menu at the top
        tk.Tk.config(self, menu=self.main_frame.menu)

    def get_lang(self):
        return self.LANG

    def get_settings(self):
        # Settings are not changed when where asked so no need to send copy.
        return self.settings


    def check_selection_validity(self, selections, filepaths):
        valid = True
        if sum(selections.values()) == 0:
            valid = False
            # TODO: Show GUI message of missing analysis selections
            if self.settings["console_print"]:
                self.cli.print_error("NO_SELECTIONS")

        if not filepaths:
            valid = False
            # TODO: Show GUI message of missing files
            if self.settings["console_print"]:
                self.cli.print_error("NO_FILES")
        return valid

    def tkvar_2_var(self, tk_vars, to_type):
        selections = {}
        if(isinstance(tk_vars, dict)):
            selections = dict(tk_vars)
            for key in selections.keys():
                if(to_type == "int"):
                    selections[key] = int(selections[key].get())
        return selections

    def analyse(self, selected_analysis, filepaths, *args, **kwargs):
        selections = self.tkvar_2_var(selected_analysis, "int")
        if not self.check_selection_validity(selections, filepaths):
            return None

        filelist = utils.crawl_dirs(filepaths, self.settings["only_leaf_files"])
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        utils.write_file(self.settings["result_path"], timestamp + "\n")

        result_page = self.main_frame.get_page(view.ResultPage)
        result_page.clear_result()  # Clears previous results
        result_page.show_info()  # Init new results with default info
        self.main_frame.show_page(view.ResultPage)

        for filepath in filelist:
            content = utils.read_file(filepath)
            filename = os.path.basename(filepath)
            dir_path = os.path.dirname(filepath)

            # No check for tree being None etc. before analysis because
            # analyses will create violation if tree is not valid. Only
            # dump checks if tree is not True.
            tree = self.model.parse_ast(content, filename)

            # Dump tree
            if(tree and self.settings["dump_tree"]):
                self.model.dump_tree(tree)

            # Call analyser
            results = self.model.analyse(
                tree,
                content,
                dir_path,
                filename,
                selections
            )

            # Format results
            formated_results = self.model.format_results(
                filename,
                filepath,
                results
            )

            # Show results and clear results
            result_page.show_results(formated_results)
            self.model.clear_analysis_data()
            formated_results.clear()

        result_page.set_line_counter(0)
        return None