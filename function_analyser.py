"""Class file. Contains FunctionAnalyser class."""
__version__ = "0.1.1"
__author__ = "RL"

import ast


import utils_lib

class FunctionAnalyser(ast.NodeVisitor):
    # Initialisation
    def __init__(self, model):
        self.model = model

    def _check_nested_function(self, node):
        """Method to check if function definition is not at a global scope."""
        if(utils_lib.get_parent_instance(node, 
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) is not None):
            self.model.add_msg("AR2-1", node.name, lineno=node.lineno)

   # Visits
    def visit_Assign(self, node, *args, **kwargs):
        """Method to find:
        1. Global variables (checking col_offset i.e. indention)
        Other ways would be check module body or does assing have FuncDef
        as parent.

        TODO Does not match:
        1. globals which are not classes and are indended.
            However utils_lib.global_test find those.
        2. Expr objects like file_handle.close()
        """
        # Global variable detection
        for var in node.targets[:]:
            if(node.col_offset == 0 or
                    utils_lib.get_parent_instance(node,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) is None):
                if(isinstance(var, ast.Attribute)):
                    self.model.add_msg("AR3-2", var.value.id, var.attr, lineno=var.lineno)
                    global_var = var.value.id
                else:
                    self.model.add_msg("AR3", var.id, lineno=var.lineno)
                    global_var = var.id

                self.model.set_global_variables(global_var, add=True)

            else:
                # This currently (doesn't?) match globals which are not classes and are indended
                # however utils_lib.global_test find those.
                # Should check if there is no class or function as parent
                pass
                # self.model.local_variables.add(var.id)
        self.generic_visit(node)


    def visit_Return(self, node, *args, **kwargs):
        """Method to check if node is:
        1. return-statement at the middle of the function.
        2. Missing return
        3. Return with missing return value
        4. Returning a constant such as 1 or "abc"
        5. Also detect (but pass) if return value is
            1. constant None, True, False etc.
            2. variable, set, tuple, list, dictionary.
            3. object or other value with attributes
            4. Function call, recursive call is detected in visit_Call method

        TODO Does not find:
        1. If there are multiple returns
        2. If return is unreachable
        3. If there are lines after the return TODO: Same thing with break and continue
            e.g. by going one level up to parent and check if there are nodes which are after the return.
        """
        if(not isinstance(node.parent_node, ast.FunctionDef)):
            self.model.add_msg("AR6-2", lineno=node.lineno)
        self.generic_visit(node)

        return_value = node.value
        if(return_value is None):  # i.e. Match return <without anything>, but not return None
            self.model.add_msg("AR6-3", lineno=node.lineno)

        # This match keyword constants None, True, False etc.
        elif((isinstance(return_value, ast.NameConstant)
                or isinstance(return_value, ast.Name))
                and hasattr(return_value, "value")):
            pass

        # This match variables, sets, tuples, lists, dictionaries.
        elif(isinstance(return_value, (ast.Name, ast.List, ast.Tuple, ast.Dict, ast.Set))):
            pass

        # This match objects and other values with attributes.
        elif(isinstance(return_value, ast.Attribute)
                or (hasattr(return_value, "func")
                and isinstance(return_value.func, ast.Attribute))):
            pass

        # This match constant strings and numbers.
        elif(isinstance(return_value, (ast.Num, ast.Str))):
            self.model.add_msg("AR6-4", lineno=node.lineno)

        # This match function calls.
        elif(isinstance(return_value, ast.Call)):
            pass
            # self.model.add_msg("AR7", lineno=node.lineno)

        else:
            #TODO: Remove test print when not needed anymore
            print("<TEST: Palautetaan jotain mitä ei tunnistettu!>", return_value.lineno)


    def visit_Call(self, node, *args, **kwargs):
        """Method to check if node is:
        1. Recursive function call.
        2. Check that sent and received parameters match
        """
        # print(node, node.func, node.func.id)
        # print(self.model.get_function_dict())
        try:
            funs = self.model.get_function_dict()
            fun = node.func.id

        # Recursive function calls.
            # if(hasattr(node, "func") and hasattr(node.func, "id")
            #     and (node.func.id == utils_lib.get_parent_instance(
            #         node, (ast.FunctionDef, ast.AsyncFunctionDef)).name)):
            if(fun == utils_lib.get_parent_instance(node,
                    (ast.FunctionDef, ast.AsyncFunctionDef)).name):
                self.model.add_msg("AR4", lineno=node.lineno)
        except AttributeError:  # This occus e.g. when function name of global variables is searched
            pass

        # Parameters check tested with Python 3.8.5
        try:
            if(fun in funs.keys()):
                has_args = True if(funs[fun].ast.args.vararg) else False
                has_kwargs = True if(funs[fun].ast.args.kwarg) else False
                default_count = len(funs[fun].ast.args.defaults)
                kw_default_count = len(funs[fun].ast.args.kw_defaults) # Currently not used
                args_count = len(funs[fun].pos_args)                        # This directly from FunctionTemplate class
                kw_only_count = len(funs[fun].kw_args) # Currently not used # This directly from FunctionTemplate class 

                call_param_count = len(node.args)
                call_kw_count = len(node.keywords) # Currently not used

                if(call_param_count < (args_count - default_count)):
                    print(f"{node.lineno}: {fun} requires at least {args_count} parameters, but {call_param_count} given.")

                elif(not has_args and (call_param_count > args_count)):
                    print(f"{node.lineno}: {fun} requires at most {args_count} parameters, but {call_param_count} given.")

                if(not has_kwargs):
                    for i in node.keywords:
                        if(i.arg not in funs[fun].kw_args):
                            print(f"{node.lineno}: in call of function {fun}, {i.arg} is invalid keyword argument.")


                # print(node.lineno, ":", call_param_count, call_kw_count, "|",
                #     args_count, default_count, has_args, kw_only_count, 
                #     kw_default_count, has_kwargs, end="---")

                # print("abc", node.args, len(node.args))
                # if(has_kwargs or has_args):
                #     print(f"pro", end="-")
                # if(args_count >= call_param_count >= (args_count - default_count)):
                #     print(f"plain", end="-")
                # if(has_args and call_param_count >= (args_count - default_count)):
                #     print(f"args", end="-")
                # print(node.lineno, end=": ")
                # if(not has_args 
                #     and (call_param_count > args_count
                #         or call_param_count < (args_count - default_count))):
                #     print(1)
                # if(has_args and call_param_count < (args_count - default_count)):
                #     print(2)

                # if((call_param_count < (args_count - default_count))
                #         or (not has_args and (call_param_count > args_count))):
        except (AttributeError, KeyError):
            print(f"Error at {node.lineno}, with {node}")
            pass
        self.generic_visit(node)


    def visit_FunctionDef(self, node, *args, **kwargs):
        """Method to find:
        1. Usage of return at the END of the function

        TODO Does not find:
        1. If there are multiple returns
        """
        # has_return = False
        # for elem in node.body:
        #     if(isinstance(elem, ast.Return)):
        #         has_return = True

        # else:  # this match if 1 layer of function body has no return, doesn't work if return is indented more
        #     if(not has_return):
        #         self.model.add_msg("AR6", node.name, lineno=node.lineno)

        if(not isinstance(node.body[-1], ast.Return)):
        #         and node.body[-1] is not ast.Yield
        #         and node.body[-1] is not ast.YieldFrom): # Doesn't work because yield (from) are inside expr node
            self.model.add_msg("AR6", node.name, lineno=node.lineno)

        self._check_nested_function(node)

        self.generic_visit(node)


    def visit_AsyncFunctionDef(self, node, *args, **kwargs):
        self._check_nested_function(node)
        self.generic_visit(node)


    def visit_Yield(self, node, *args, **kwargs):
        """Method to detect usage of yield."""
        self.model.add_msg("AR6-1",
            "yield",
            utils_lib.get_parent_instance(node, (ast.FunctionDef, ast.AsyncFunctionDef)).name,
            lineno=node.lineno)


    def visit_YieldFrom(self, node, *args, **kwargs):
        """Method to detect usage of yield from."""
        self.model.add_msg("AR6-1",
            "yield from",
            utils_lib.get_parent_instance(node, (ast.FunctionDef, ast.AsyncFunctionDef)).name,
            lineno=node.lineno)