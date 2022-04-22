import sys
import os
import scanner
import pydot
import ply.yacc as yacc
from symtab import (
    SYMBOL_TABLES,
    pop_scope,
    push_scope,
    new_scope,
    get_current_symtab,
)
from draw import make_ast,Node

INIT_PARAMETERS={"type":[],"declarations":[]}
LAST_FUNCTION = None
INCOMING_FUNCTION = False
ERROR = []

tokens = scanner.scanner.tokens
literals = scanner.scanner.literals
flag_for_error = 0

start = "start"

def p_primary_expression(p):
    """primary_expression : id
    | int
    | str
    | bool
    | char
    | '(' expression ')' """
    if len(p)==4:
        if isinstance(p[2],list):
            if len(p[2])>1:
                err_msg = "Comma saperated multiple expressions in line "+str(p.lineno(1))
                ERROR.append(err_msg)
                raise SyntaxError
            p[0]=p[2][0]
        else:
            p[0] = p[2]
    else:
        p[0]=p[1]
    
def p_id(p):
    """id : ID"""
    symtab = get_current_symtab()
    i = symtab.lookup(p[1])
    if i is None:
        err_msg = "Identifier "+p[1]+" not declared on line "+str(p.lineno(1))
        ERROR.append(err_msg)
        raise SyntaxError
    arr = 0
    if i["kind"]==0:
        _type = i["type"]
        arr = i["is_array"]
    elif i["kind"]==1:
        _type = i["return type"]
    p[0] = Node("identifier",_type,arr,_value=p[1])

def p_str(p):
    """str : STRING"""
    p[0] = Node("constant","char",is_array=1,_value=p[1])
    
def p_int(p):
    """int : INTEGER"""
    p[0] = Node("constant","int",_value=p[1])
    
def p_char(p):
    """char : CHARACTER"""
    p[0] = Node("constant","char",_value=p[1])
    
def p_bool(p):
    """bool : TRUE
    | FALSE"""
    p[0] = Node("constant","bool",_value=p[1])

def p_postfix_expression(p):
    """postfix_expression : primary_expression
    | postfix_expression '[' expression ']'
    | postfix_expression '(' ')'
    | postfix_expression '(' argument_expression_list ')'
    | postfix_expression INC
    | postfix_expression DEC"""
    symtab=get_current_symtab()
    if len(p)==2:
        p[0]=p[1]
    elif len(p)==3:
        name = p[2]+'('+p[1]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible type for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1]]})
    elif len(p)==4:
        name = p[1]._value+"()"
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible type for "+p[1]._value+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:None})       
    elif len(p)==5:
        if p[2]=='(':
            name = p[1]._value+'('+','.join([i._type for i in p[3]])+')'
            i = symtab.lookup(name)
            if i is None:
                err_msg = "Incompatible type for "+p[1]._value+" in line "+str(p.lineno(1))
                ERROR.append(err_msg)
                raise SyntaxError
            p[0] = Node("function call",i["return type"],children={i["name"]:p[3]})
        else:
            name = '[]('+p[1]._type+','+p[3]._type+')'
            i = symtab.lookup(name)
            if i is None:
                err_msg = "Incompatible type for [] in line "+str(p.lineno(1))
                ERROR.append(err_msg)
                raise SyntaxError
            p[0] = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})
    
def p_argument_expression_list(p):
    """argument_expression_list : assignment_expression
    | argument_expression_list ',' assignment_expression"""
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[3]]

def p_unary_expression(p):
    """unary_expression : postfix_expression
    | INC unary_expression
    | DEC unary_expression
    | unary_operator unary_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        symtab=get_current_symtab()
        name = p[1]+'('+p[2]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible type for "+p[1]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[2]]})

def p_unary_operator(p):
    """unary_operator : '&'
    | '*'
    | '+'
    | '-'
    | '~'
    | '!'"""
    p[0]=p[1]


def p_multiplicative_expression(p):
    """multiplicative_expression : unary_expression
    | multiplicative_expression '*' unary_expression
    | multiplicative_expression '/' unary_expression
    | multiplicative_expression '%' unary_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        symtab=get_current_symtab()
        name = p[2]+'('+p[1]._type.lower()+','+p[3]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})

def p_additive_expression(p):
    """additive_expression : multiplicative_expression
    | additive_expression '+' multiplicative_expression
    | additive_expression '-' multiplicative_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        symtab=get_current_symtab()
        name = p[2]+'('+p[1]._type.lower()+','+p[3]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})

def p_relational_expression(p):
    """relational_expression : additive_expression
    | relational_expression '<' additive_expression
    | relational_expression '>' additive_expression
    | relational_expression LE additive_expression
    | relational_expression GE additive_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        symtab=get_current_symtab()
        name = p[2]+'('+p[1]._type.lower()+','+p[3]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})

def p_equality_expression(p):
    """equality_expression : relational_expression
    | equality_expression EQUAL relational_expression
    | equality_expression NE relational_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        symtab=get_current_symtab()
        name = p[2]+'('+p[1]._type.lower()+','+p[3]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})

def p_and_expression(p):
    """and_expression : equality_expression
    | and_expression '&' equality_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        symtab=get_current_symtab()
        name = p[2]+'('+p[1]._type.lower()+','+p[3]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})

def p_exclusive_or_expression(p):
    """exclusive_or_expression : and_expression
    | exclusive_or_expression '^' and_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        symtab=get_current_symtab()
        name = p[2]+'('+p[1]._type.lower()+','+p[3]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})

def p_inclusive_or_expression(p):
    """inclusive_or_expression : exclusive_or_expression
    | inclusive_or_expression '|' exclusive_or_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        symtab=get_current_symtab()
        name = p[2]+'('+p[1]._type.lower()+','+p[3]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})

def p_logical_and_expression(p):
    """logical_and_expression : inclusive_or_expression
    | logical_and_expression AND inclusive_or_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        symtab=get_current_symtab()
        name = p[2]+'('+p[1]._type.lower()+','+p[3]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})

def p_logical_or_expression(p):
    """logical_or_expression : logical_and_expression
    | logical_or_expression OR logical_and_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        symtab=get_current_symtab()
        name = p[2]+'('+p[1]._type.lower()+','+p[3]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})


def p_assignment_expression(p):
    """assignment_expression : logical_or_expression
    | unary_expression assignment_operator assignment_expression"""
    if len(p)==2:
        p[0]=p[1]
    else:
        if len(p[2])>1:
            symtab=get_current_symtab()
            name = p[2][0]+'('+p[1]._type.lower()+','+p[3]._type.lower()+')'
            i = symtab.lookup(name)
            if i is None:
                err_msg = "Incompatible types for "+p[2][0]+" in line "+str(p.lineno(1))
                ERROR.append(err_msg)
                raise SyntaxError
            temp = Node("function call",i["return type"],children={i["name"]:[p[1],p[3]]})
        else:
            temp = p[3]
        symtab=get_current_symtab()
        name = '='+'('+p[1]._type.lower()+','+temp._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for = in line "+str(p.lineno(1))+" "+name
            ERROR.append(err_msg)
            raise SyntaxError
        temp = Node("function call",i["return type"],children={i["name"]:[p[1],temp]})

def p_assignment_operator(p):
    """assignment_operator : '='
    | MUL_EQ
    | DIV_EQ
    | MOD_EQ
    | ADD_EQ
    | SUB_EQ
    | AND_EQ
    | XOR_EQ
    | OR_EQ"""
    p[0] = p[1]

def p_expression(p):
    """expression : assignment_expression
    | expression ',' assignment_expression"""
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[3]]

def p_constant_expression(p):
    """constant_expression : logical_or_expression"""
    p[0] = p[1]

def p_declaration(p):
    """declaration : type_specifier init_declarator_list ';'"""
    for i in p[2]:
        i._type = p[1].lower()
    p[0] = Node("statement","declaration",_value=p[2])
    symtab = get_current_symtab()
    for i in p[2]:
        entry = {"name":i._value,"type":i._type,"ptr_level":i.ptr_level,"is_array":i.is_array}
        if (i.children is not None) and (i.children.get("dims",None) is not None):
            entry["dimensions"] = i.children["dims"]
        symtab.insert(entry,0)


def p_init_declarator_list(p):
    """init_declarator_list : declarator
    | init_declarator_list ',' declarator"""
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[3]]

def p_type_specifier(p):
    """type_specifier : VOID
    | CHAR
    | INT
    | BOOL"""
    p[0] = p[1]


def p_declarator(p):
    """declarator : pointer direct_declarator
    | direct_declarator"""
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = p[2]
        p[0].ptr_level = p[2].ptr_level+p[1]

def p_direct_declarator(p):
    """direct_declarator : ID
    | '(' declarator ')'
    | direct_declarator '[' constant_expression ']'
    | direct_declarator '[' ']'
    | direct_declarator '(' parameter_list ')'
    | direct_declarator '(' ')'"""
    if len(p)==2:
        p[0]=Node("identifier","undeclared",_value=p[1])
    elif len(p)==4:
        if p[1]=='(':
            p[0]=p[2]
        elif p[2]=='(':
            if p[1].name=="identifier" and p[1]._type=="undeclared" and p[1].is_array==0:
                p[0]=Node("function","undeclared",_value=p[1]._value,children={"parameters":[]})
            else:
                err_msg="Error in function name in function declaration in line "+str(p.lineno(1))
                ERROR.append(err_msg)
                raise SyntaxError
        elif p[2]=='[':
            if p[1].name=="identifier" and p[1]._type=="undeclared":
                p[1].is_array=1
                p[1].ptr_level+=1
                if not p[1].children is None and p[1].children.get("dims",False):
                    p[1].children["dims"].append(None)
                else:
                    p[1].children = {"dims":[None,]}  
                p[0]=p[1]
            else:
                err_msg="Error in array declaration in line "+str(p.lineno(1))
                ERROR.append(err_msg)
                raise SyntaxError
    else:
        if p[2]=='(':
            if p[1].name=="identifier" and p[1]._type=="undeclared" and p[1].is_array==0:
                p[0]=Node("function","undeclared",_value=p[1]._value,children={"parameters":p[3]})
            else:
                err_msg="Error in function name in function declaration in line "+str(p.lineno(1))
                ERROR.append(err_msg)
                raise SyntaxError
        elif p[2]=='[':
            if p[1].name=="identifier" and p[1]._type=="undeclared" and p[3]._type.lower()=="int":
                p[1].is_array=1
                p[1].ptr_level+=1
                ndims = 0
                if p[3].name=="constant" and p[3]._type=="int":
                    ndims = p[3]._value
                else:
                    ndims = p[3]
                if not p[1].children is None and p[1].children.get("dims",False):
                    p[1].children["dims"].append(ndims)
                else:
                    p[1].children = {"dims":[ndims,]}  
                p[0]=p[1]
            else:
                err_msg="Error in array declaration in line "+str(p.lineno(1))
                ERROR.append(err_msg)
                raise SyntaxError


def p_pointer(p):
    """pointer : '*'
    | '*' pointer"""
    if len(p)==2:
        p[0] = 1
    else:
        p[0] = 1+p[1]

def p_parameter_list(p):
    """parameter_list : parameter_declaration
    | parameter_list ',' parameter_declaration"""
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[3]]

def p_parameter_declaration(p):
    """parameter_declaration : type_specifier declarator"""
    global INIT_PARAMETERS
    INIT_PARAMETERS["type"].append(p[1])
    INIT_PARAMETERS["declarations"].append(p[2])
    p[0] = Node("parameter",p[1],_value=p[2])

def p_statement(p):
    """statement : input_statement
    | output_statement
    | compound_statement
    | expression_statement
    | selection_statement
    | iteration_statement
    | jump_statement"""
    p[0] = p[1]

def p_compound_statement(p):
    """compound_statement : lbrace statement_list rbrace
    | lbrace declaration_list rbrace
    | lbrace declaration_list statement_list rbrace"""
    if len(p)==4:
        p[0] = Node("statement","compound",_value=p[2],children={"local scope":p[1]})
    else:
        p[0] = Node("statement","compound",_value = p[2]+p[3],children={"local scope":p[1]})

def p_declaration_list(p):
    """declaration_list : declaration
    | declaration_list declaration"""
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[2]]

def p_statement_list(p):
    """statement_list : statement
    | statement_list statement"""
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[2]]

def p_expression_statement(p):
    """expression_statement : ';'
    | expression ';'"""
    if len(p)==2:
        p[0] = Node("statement","expression")
    else:
        p[0] = Node("statement","expression",_value=p[1])

def p_selection_statement(p):
    """selection_statement : IF '(' expression ')' statement
    | IF '(' expression ')' statement ELSE statement"""
    p[0] = Node("statement","IF",children={"condition":p[3],"IF_BLOCK":p[5],"ELSE_BLOCK":None})
    if len(p)==8:
        p[0].children["ELSE_BLOCK"]=p[7]

def p_iteration_statement(p):
    """iteration_statement : while_st
    | for_st"""
    p[0] = p[1]

def p_while_st(p):
    """while_st : WHILE '(' expression ')' statement"""
    p[0] = Node("statement","WHILE",children={"condition":p[3], "BLOCK":p[5]})

def p_for_st(p):
    """for_st : FOR '(' expression_statement expression_statement expression ')' statement"""
    p[0] = Node("statement","FOR",children={"init":p[3],"condition":p[4],"update":p[5], "BLOCK":p[7]})

def p_jump_statement(p):
    """jump_statement : CONTINUE ';'
    | BREAK ';'
    | RETURN ';'
    | RETURN expression ';'"""
    p[0] = Node("statement","jump",_value=p[1])
    if len(p)==4:
        p[0].children = {"return":p[2]}

def p_start(p):
    """start : translation_unit"""
    p[0] = Node("start","None",_value=p[1])

def p_translation_unit(p):
    """translation_unit : external_declaration
    | translation_unit external_declaration"""
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[2]]

def p_external_declaration(p):
    """external_declaration : function_definition
    | declaration"""
    p[0] = p[1]

def p_function_definition(p):
    """function_definition : type_specifier declarator compound_statement"""
    global INCOMING_FUNCTION,LAST_FUNCTION
    if p[2].name!="function" and p[2]._type!="undeclared":
        err_msg = "Error in function declaration at line "+str(p.lineno(1))
        ERROR.append(err_msg)
        raise SyntaxError
    p[2]._type=p[1].lower()
    param = [i._type+'*'*i._value.ptr_level for i in p[2].children["parameters"]]
    entry = {"name":p[2]._value,"return type":p[1].lower(),"ptr_level":p[2].ptr_level,"parameter types":param,"local scope":p[3].children["local scope"]}
    symtab = get_current_symtab()
    symtab.insert(entry,1)
    INCOMING_FUNCTION=True
    LAST_FUNCTION = entry["name"]+'('+','.join(entry["parameter types"]) +')'
    p[2].children["BLOCK"]=p[3]
    p[0]=p[2]
    
def p_input_statement(p):
    """input_statement : CIN IN id ';'"""
    p[0] = Node("statement","input",_value=p[3])

def p_output_statement(p):
    """output_statement : COUT output_list ';'"""
    p[0]=Node("statement","output",_value=p[2])
    
def p_output_list(p):
    """output_list : OUT primary_expression
    | output_list OUT primary_expression"""
    if len(p)==3:
        p[0]=[p[2]]
    else:
        p[0]=p[1]+[p[3]]

#check
def p_lbrace(p):
    """lbrace : '{'"""
    global INCOMING_FUNCTION, LAST_FUNCTION
    push_scope(new_scope(get_current_symtab(), LAST_FUNCTION if INCOMING_FUNCTION else None))
    symTab = get_current_symtab()
    global INIT_PARAMETERS
    if len(INIT_PARAMETERS["type"])!=0:
        for i in range(len(INIT_PARAMETERS["type"])):
            curr = INIT_PARAMETERS["declarations"][i]
            if curr.name!="identifier":
                err_msg = "Wrong parameter used in line "+str(p.lineno(1))
                ERROR.append(err_msg)
                raise SyntaxError
            if curr.children is None:
                dims=None
            else:
                dims = curr.children.get("dims",None)
            entry = {"name":curr._value,"type":INIT_PARAMETERS["type"][i].lower(),"is_array":curr.is_array,"ptr_level":curr.ptr_level,"dimensions":dims}
            symTab.insert(entry,0)
        INIT_PARAMETERS = {"type":[],"declarations":[]}
    p[0] = symTab


def p_rbrace(p):
    """rbrace : '}'"""
    global LAST_POPPED_TABLE,INCOMING_FUNCTION,LAST_FUNCTION
    LAST_POPPED_TABLE = pop_scope()
    while not LAST_POPPED_TABLE is None:
        if LAST_POPPED_TABLE in SYMBOL_TABLES:
            break
        LAST_POPPED_TABLE=LAST_POPPED_TABLE.parent
    if LAST_POPPED_TABLE==None:
        INCOMING_FUNCTION=False
    else:
        LAST_FUNCTION = LAST_POPPED_TABLE.func_scope

def p_error(p):
    global flag_for_error
    flag_for_error = 1

    if p is not None:
        print("error at line no:  %s :: %s" % ((p.lineno), (p.value)))
        parser.errok()
    else:
        print("Unexpected end of input")

parser = yacc.yacc()

def populate_global_symbol_table():
    table = get_current_symtab()
    for op in ("+", "-"):
        for _type in ["INT","CHAR"]:
            _type = _type.lower()
            table.insert({ "name": op, "return type": _type, "parameter types": [_type, _type]}, 1)

    for op in ("<", ">", "<=", ">=", "==", "!=","&&", "||"):
        for _type in ["INT","BOOL"]:
            _type = _type.lower()
            table.insert({"name": op, "return type": "int", "parameter types": [_type, _type]}, 1)

    for op in ("&", "|","^","~"):
        for _type in ["INT","CHAR","BOOL"]:
            _type = _type.lower()
            table.insert({"name": op, "return type": "int", "parameter types": [_type]}, 1)
            
    for _type in ["INT","CHAR","BOOL"]:
        _type = _type.lower()
        table.insert({"name": '!', "return type": "int", "parameter types": [_type]}, 1)
        
    for _type in ["INT","CHAR","BOOL"]:
        _type = _type.lower()
        table.insert({"name": '=', "return type": "int", "parameter types": [_type,_type]}, 1)
            
    table.insert({"name": '-', "return type": "int", "parameter types": ['int']}, 1)
    
    for op in ("%", "/", "*"):
        table.insert({"name": op, "return type": "int", "parameter types": ["int","int"], }, 1)

    for op in ("++", "--"):
        table.insert({"name": op,"return type": "int", "parameter types": ["int"]}, 1)
        
    for op in ("in","out"):
        for _type in ["INT","CHAR","BOOL"]:
            _type = _type.lower()
            table.insert({"name": op, "return type": "int", "parameter types": [_type]}, 1)
            
    for _type in ["INT","CHAR","BOOL"]:
        _type = _type.lower()
        table.insert({"name": "[]", "return type": _type, "parameter types": [f"{_type}*", "int"]}, 1)

if __name__ == "__main__":
    if(len(sys.argv) == 2):
        file = sys.argv[1]
        fl = open(file,'r')
        inp = fl.read()
        push_scope(new_scope(get_current_symtab()))
        populate_global_symbol_table()
        result = parser.parse(inp)
        if len(ERROR)==0:
            pop_scope()
            graph = pydot.Dot("my_graph", graph_type='graph')
            make_ast(graph,result)
            graph.write_dot('AST.dot')
        else:
            for err in ERROR:
                print(err)   
