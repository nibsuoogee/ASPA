"""Class file. Contains PreAnalyser class."""
__version__ = "0.0.1"
__author__ = "RL"

import ast

import utils_lib as utils

class PreAnalyser(ast.NodeVisitor):
    """
    TODO:
    1. Identify lib and main files
    2. Count that there are >= 2 function in lib file
    """
    def __init__(self, library=None):
        self.import_dict = dict()
        self.class_dict = dict()
        self.function_dict = dict()
        self.global_list = list()
        self.library = library


   # Getters
    def get_import_dict(self):
        return dict(self.import_dict)

    def get_function_dict(self):
        return dict(self.function_dict)

    def get_class_dict(self):
        return dict(self.class_dict)

    def get_global_list(self):
        return list(self.global_list)

   # General methods
    def clear_all(self):
        self.import_dict.clear()
        self.function_dict.clear()
        self.class_dict.clear()
        self.global_list.clear()

    # TODO: General store node function?
    def _store_class(self, node):
        key = node.name
        parent = utils.get_parent_instance(node, 
            (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        if(parent):
            key = f"{parent.name}.{key}"
        if(self.library):
            key = f"{self.library}.{key}"
        self.class_dict[key] = utils.ClassTemplate(
            node.name, node.lineno, node)

    def _store_import(self, node, name, import_from=False):
        if(self.library):
            name = f"{self.library}.{name}"
        if(not name in self.import_dict.keys()):
            self.import_dict[name] = list()
        self.import_dict[name].append(utils.ImportTemplate(
            name, node.lineno, node, import_from=import_from))

    def _store_function(self, node):
        key = node.name
        pos_args = [i.arg for i in node.args.args]
        kw_args = [i.arg for i in node.args.kwonlyargs]

        parent = utils.get_parent_instance(node, 
            (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        if(parent):
            key = f"{parent.name}.{key}"
        if(self.library):
            key = f"{self.library}.{key}"
        #  TODO: If key exist then there are two identically named functions in same scope
        # Could use similar list solution as with imports
        self.function_dict[key] = utils.FunctionTemplate(
            node.name, node.lineno, node, pos_args, kw_args)

   # Visits
    # Imports
    def visit_Import(self, node, *args, **kwargs):
        for i in node.names:
            self._store_import(node, i.name, import_from=False)
        self.generic_visit(node)

    def visit_ImportFrom(self, node, *args, **kwargs):
        self._store_import(node, node.module, import_from=True)
        self.generic_visit(node)

    # Functions
    def visit_FunctionDef(self, node, *args, **kwargs):
        self._store_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node, *args, **kwargs):
        self._store_function(node)
        self.generic_visit(node)

    # Classes
    def visit_ClassDef(self, node, *args, **kwargs):
        self._store_class(node)
        self.generic_visit(node)
