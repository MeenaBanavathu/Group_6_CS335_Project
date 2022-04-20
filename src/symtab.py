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
        self._structs = dict()
        self._classes = dict()
        self._custom_types = dict()
        self.parent = parent
        self.table_number = TABLENUMBER
        TABLENUMBER += 1

        if parent is None:
            self.table_name = "GLOBAL"
        else:
            self.table_name = f"BLOCK {self.table_number}"

    def insert(self, entry, kind=0):
        # Variables (ID) -> {"name", "type", "value", "is_array", "dimensions", "pointer_lvl"}
        # Functions (FN) -> {"name", "return type", "parameter types"}->symtab
        # Structs (ST)   -> {"name", "field names", "field types", "field values"}->symtab
        # Classes (CL)   -> {"name", ... TBD}->symtab
        global DATATYPE

        prev_entry = self.lookup(entry["name"])

        if prev_entry is None:
            name = entry["name"]
            entry["kind"] = kind
            entry["pointer_lvl"] = entry.get("pointer_lvl", 0)
            if kind == 0:
                t = self.lookup_type(entry["type"])
                if not t:
                    raise Exception(f"{entry['type']}: not a valid data type")
                entry["size"] = t
                entry["value"] = entry.get("value", get_default_value(entry["type"]))
                #check
                entry["offset"] = compute_offset_size(entry["size"], entry["is_array"], entry.get("dimensions", []), entry, t)
                #check
                if entry["is_array"]:
                    dims = entry["dimensions"]
                    ndims = []
                    for dim in dims:
                        if dim == "variable":
                            continue
                        if isinstance(dim, str):
                            _l = self.lookup(dim)
                            if _l["type"] != "int":
                                raise Exception
                            ndims.append(dim)
                        else:
                            if dim["type"] != "int":
                                raise Exception
                            ndims.append(dim["value"])
                    entry["dimensions"] = ndims

                self._variables[name] = entry

            elif kind == 1:
                self._functions[name] = entry
                new_name = name+'('+",".join(entry["parameter types"]) +')'
                self._function_name[new_name] = entry

            elif kind == 2:
                if len(set(entry["field names"])) != len(entry["field names"]):
                    raise Exception("Non Unique Field Names detected")
                self._structs[name] = entry
                self._custom_types[f"struct {name}"] = entry

            elif kind == 3:
                # Class
                self._symtab_classes[name] = entry
                self._custom_types[f"class {name}"] = entry

            else:
                raise Exception(f"{kind} is not a valid kind of identifier")

            return True, entry
        return False, prev_entry
        # After Storage
        # Variables (ID) -> {"name", "type", "value", "is_array", "dimensions", "kind", "size", "offset", "pointer_lvl"}
        # Functions (FN) -> {"name", "return type", "parameter types", "kind", "local scope"}
    

    def lookup_current_table(self, name):
        res = self._variables.get(name, None)
        res = self._functions.get(name, None) if res is None else res
        res = self._function_name.get(name, None) if res is None else res
        res = self._struct.get(name, None) if res is None else res
        res = self._class.get(name, None) if res is None else res
        return res
    
    def _lookup_type(self,name):
        t = self._custom_types.get(name, None)
        return self.parent._lookup_type(name) if t is None and self.parent else t
    
    def lookup_type(self, name):
        t = DATATYPE.get(name,None)
        return self._lookup_type(name) if t is None else t

    def lookup(self, name):
        res = self.lookup_current_table(name)
        return self.parent.lookup(name) if res is None and self.parent else res

#check
    def display(self):
        # Simple Pretty Printer
        global num_display_invocations
        print()
        print("-" * 100)
        print(f"SYMBOL TABLE: {self.table_name}, TABLE NUMBER: {self.table_number}, FUNCTION SCOPE: {self.func_scope}")
        print("-" * 51)
        print(" " * 20 + " Variables " + " " * 20)
        print("-" * 51)
        for k, v in self._symtab_variables.items():
            if v["name"][: min(2, len(k))] == "__":
                continue
            print(
                f"Name: {k}, Type: {v['type'] + '*' * v['pointer_lvl']}, Size: {v['size']}, Offset: {v['offset']}"
                + ("" if not v["is_array"] else f", Dimensions: {v['dimensions']}")
            )
        print("-" * 51)
        print(" " * 20 + " Functions " + " " * 20)
        print("-" * 51)
        for k, v in self._symtab_functions.items():
            if v["name"][: min(1, len(k))] == "__" or not v["name"][0].isalpha():
                continue
            print(
                f"Name: {v['name']}, Return: {v['return type']}, Parameters: {v['parameter types']}, Name Resolution: {k}"
            )
        print("-" * 100)
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
                        "SIZE",
                        "OFFSET",
                        "DIMENSIONS",
                        "RETURN TYPE",
                        "PARAMETERS",
                        "NAME RESOLUTION",
                    ]
                )
                num_display_invocations += 1
            for k, v in self._symtab_variables.items():
                if v["name"][: min(2, len(k))] == "__":
                    continue

                if not v["is_array"]:
                    sym_writer.writerow(
                        [
                            f"{self.table_name}",
                            f"{self.func_scope}",
                            "Variable",
                            f"{k}",
                            f"{v['type'] + '*' * v['pointer_lvl']}",
                            f"{v['size']}",
                            f"{v['offset']}",
                            "",
                            "",
                            "",
                            "",
                        ]
                    )
                else:
                    sym_writer.writerow(
                        [
                            f"{self.table_name}",
                            f"{self.func_scope}",
                            "Variable",
                            f"{k}",
                            f"{v['type'] + '*' * v['pointer_lvl']}",
                            f"{v['size']}",
                            f"{v['offset']}",
                            f"{v['dimensions']}",
                            "",
                            "",
                            "",
                        ]
                    )

            for k, v in self._symtab_functions.items():
                if v["name"][: min(1, len(k))] == "__" or not v["name"][0].isalpha():
                    continue
                sym_writer.writerow(
                    [
                        f"{self.table_name}",
                        f"{self.func_scope}",
                        "Function",
                        f"{v['name']}",
                        "",
                        "",
                        "",
                        "",
                        f"{v['return type']}",
                        f"{v['parameter types']}",
                        f"{k}",
                    ]
                )


SYMBOL_TABLES = []

STATIC_VARIABLE_MAPS = {}


def pop_scope():
    global SYMBOL_TABLES
    s = SYMBOL_TABLES.pop()
    s.display()
    return s


def push_scope(s):
    global SYMBOL_TABLES
    SYMBOL_TABLES.append(s)


def new_scope(parent=None, function_scope=None):
    return SymbolTable(parent, function_scope)


def get_current_symtab():
    global SYMBOL_TABLES
    return None if len(SYMBOL_TABLES) == 0 else SYMBOL_TABLES[-1]

#check
def compute_offset_size(dsize, is_array, entry):
    if not is_array:
        return dsize
    else:
        offset = [DATATYPE[entry["type"].upper()]]
        for i, d in enumerate(reversed(entry["dimensions"])):
            if i is not  len(entry["dimensions"]) - 1 :
                offset.append(offset[i]* int(d["value"]))
        return offset[::-1]

#check
def compute_storage_size(entry, typeentry):
    _c = entry["type"].count("*")
    if _c > 0:
        t = "".join(filter(lambda x: x != "*", entry["type"])).strip()
        return compute_storage_size({"type": t, "pointer_lvl": _c}, get_current_symtab().lookup_type(t))
    global DATATYPE
    if entry.get("is_array", False):
        prod = DATATYPE[entry["type"].upper()]
        for d in entry["dimensions"]:
            if d == "variable":
                return "var"
            prod*=int(d["value"])
        return prod
    if entry.get("pointer_lvl", 0) > 0:
        return 8
    if entry["type"].startswith("struct "):
        size = 0
        symTab = get_current_symtab()
        temp = "".join(filter(lambda x: x != "*", entry["type"])).strip()
        typeentry = symTab.lookup_type(temp)
        for t in typeentry["field types"]:
            size += compute_storage_size({"type": t}, symTab.lookup_type(t))
        return size
    if typeentry is None:
        s = DATATYPE[entry["type"].upper()]
        return s
    else:
        raise NotImplementedError
    return 0

TMP_VAR_COUNTER=0

def get_tmp_var(vartype=None, symTab=None):
    global TMP_VAR_COUNTER
    TMP_VAR_COUNTER += 1
    vname = f"__tmp_var_{TMP_VAR_COUNTER}"
    if vartype is not None:
        symTab = get_current_symtab() if symTab is None else symTab

        ptr_level = vartype.count("*")
        if ptr_level > 0:
            symTab.insert(
                {
                    "name": vname,
                    "type": vartype[:-ptr_level],
                    "is_array": False,
                    "dimensions": [],
                    "pointer_lvl": ptr_level,
                }
            )
        else:
            symTab.insert(
                {
                    "name": vname,
                    "type": vartype,
                    "is_array": False,
                    "dimensions": [],
                }
            )
    return vname

def get_default_value(_type):
    if _type.upper()=="INT":
        return 0
    elif _type.upper()=="CHAR":
        return ''
    elif _type[-1] == "*":
        return "NULL"
    else:
    	return -1
