import csv
import os

DATATYPE = {
    "VOID": 0,
    "CHAR": 1,
    "INT": 4,
    "BOOL": 1
}

TABLENUMBER = 0

num_display_invocations = 0

def get_default_value(_type):
    if _type.upper()=="INT":
        return 0
    elif _type.upper()=="CHAR":
        return ''
    elif _type[-1] == "*":
        return "NULL"
    else:
    	return -1

class SymbolTable:
    # kind = 0 for ID
    #        1 for FN
    #        2 for ST
    #        3 for CL
    def __init__(self, parent=None, function_scope=None):
        global TABLENUMBER
        self.func_scope = function_scope if TABLENUMBER != 0 else "GLOBAL"
        self._variables = dict()
        self._functions = dict()
        self._function_name = dict()
        self.parent = parent
        self.table_number = TABLENUMBER
        TABLENUMBER += 1

        if parent is None:
            self.table_name = "GLOBAL"
        else:
            self.table_name = f"BLOCK {self.table_number}"

    def insert(self, entry, kind=0):
        # Variables (ID) -> {"name", "type", "value", "is_array", "dimension", "ptr_level"},"kind"
        # Functions (FN) -> {"name", "return type", "parameter types","ptr_level"},"kind","local scope":symtab
        global DATATYPE

        prev_entry = self.lookup(entry["name"])

        if prev_entry is None:
            name = entry["name"]
            entry["kind"] = kind
            entry["ptr_level"] = entry.get("ptr_level", 0)
            if kind == 0:
                t = self.lookup_type(entry["type"])
                if not t:
                    raise Exception(f"{entry['type']}: not a valid data type")
                entry["size"] = t
                entry["value"] = entry.get("value", get_default_value(entry["type"]))
                entry["is_array"] = entry.get("is_array",0)
                entry["dimensions"] = entry.get("dimensions",None)
                self._variables[name] = entry

            elif kind == 1:
                entry["local_scope"] = entry.get("local scope",None)
                self._functions[name] = entry
                new_name = name+'('+",".join(entry["parameter types"]) +')'
                self._function_name[new_name] = entry

            else:
                raise Exception(f"{kind} is not a valid kind of identifier")

            return True, entry
        return False, prev_entry
    

    def lookup_current_table(self, name):
        res = self._variables.get(name, None)
        res = self._function_name.get(name, None) if res is None else res
        return res
    
    def lookup_type(self, name):
        t = DATATYPE.get(name.upper(),None)
        return t

    def lookup(self, name):
        res = self.lookup_current_table(name)
        return self.parent.lookup(name) if res is None and self.parent else res

    def display(self,disp=0):
        global num_display_invocations
        if disp==1:
            print()
            print("-" * 100)
            print(f"SYMBOL TABLE: {self.table_name}, TABLE NUMBER: {self.table_number}, FUNCTION SCOPE: {self.func_scope}")
            print()
            print(" Variables:: ")
            print()
            for k, v in self._variables.items():
                print(f"Name: {k}, Type: {v['type'] + '*' * v.get('pointer_lvl',0)}")
            print()
            print("Functions:: ")
            print()
            for k, v in self._function_name.items():
                print(f"Name: {v['name']}, Return: {v['return type']}, Parameters: {v['parameter types']}, Name Resolution: {k}")
            print()

        # printing symbol tables in csv
        if num_display_invocations == 0:
            if os.path.isfile("symtables.csv"):
                os.remove("symtables.csv")

        with open("symtables.csv", mode="a+") as sym_file:
            sym_writer = csv.writer(sym_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            if num_display_invocations == 0:
                sym_writer.writerow(
                    [
                        "SYMBOL TABLE",
                        "FUNCTION SCOPE",
                        "VARIABLE/FUNCTION",
                        "NAME",
                        "TYPE",
                        "RETURN TYPE",
                        "PARAMETERS",
                    ]
                )
                num_display_invocations += 1
            for k, v in self._variables.items():
                sym_writer.writerow(
                    [
                        f"{self.table_name}",
                        f"{self.func_scope}",
                        "Variable",
                        f"{k}",
                        f"{v['type'] + '*' * v.get('pointer_lvl',0)}",
                        "",
                        "",
                    ]
                )
            for k, v in self._function_name.items():
                sym_writer.writerow(
                    [
                        f"{self.table_name}",
                        f"{self.func_scope}",
                        "Function",
                        f"{k}",
                        "",
                        f"{v['return type'] + '*' * v.get('pointer_lvl',0)}",
                        " ".join(v["parameter types"]),
                    ]
                )

SYMBOL_TABLES = []

STATIC_VARIABLE_MAPS = {}


def pop_scope():
    global SYMBOL_TABLES
    s = SYMBOL_TABLES.pop()
    s.display(1)
    return s


def push_scope(s):
    global SYMBOL_TABLES
    SYMBOL_TABLES.append(s)


def new_scope(parent=None, function_scope=None):
    return SymbolTable(parent, function_scope)


def get_current_symtab():
    global SYMBOL_TABLES
    return None if len(SYMBOL_TABLES) == 0 else SYMBOL_TABLES[-1]
