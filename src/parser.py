import sys
import os
import scanner
import ply.yacc as yacc
from symtab import (
    pop_scope,
    push_scope,
    new_scope,
    get_current_symtab,
    get_default_value,
    DATATYPE,
    SYMBOL_TABLES,
)

class Node:
    def __init__(self,name,_type,is_array=0,children=None,value=None):
        self.name = name
        self._type = _type
        self.is_array = is_array
        self.value = value
        self.children = children

ERROR = []

tokens = scanner.scanner.tokens
literals = scanner.scanner.literals
flag_for_error = 0

start = "translation_unit"

def p_primary_expression(p):
    """primary_expression : id
    | int
    | str
    | bool
    | char
    | '(' expression ')' """
    if len(p)==4:
        p[0]=p[2]
    else:
        p[0]=p[1]
    
def p_id(p):
    """id : ID"""
    symtab = get_current_symtab()
    i = symtab.lookup(p[1])
    if i is None:
        err_msg = "Identifier not declared on line "+str(p.lineno(1))
        ERROR.append(err_msg)
        raise SyntaxError
    arr = 0
    if i["kind"]==0:
        _type = i["type"]
        arr = i["is_array"]
    elif i["kind"]==1:
        _type = i["return type"]
    p[0] = Node("identifier",_type,arr,value=p[1])

def p_str(p):
    """str : STRING"""
    p[0] = Node("constant","char",is_array=1,value=p[1])
    
def p_int(p):
    """int : INTEGER"""
    p[0] = Node("constant","int",value=p[1])
    
def p_char(p):
    """char : CHARACTER"""
    p[0] = Node("constant","char",value=p[1])
    
def p_bool(p):
    """bool : TRUE
    | FALSE"""
    p[0] = Node("constant","bool",value=p[1])

def p_postfix_expression(p):
    """postfix_expression : primary_expression
    | postfix_expression '[' expression ']'
    | postfix_expression '(' ')'
    | postfix_expression '(' argument_expression_list ')'
    | postfix_expression INC
    | postfix_expression DEC"""
    if len(p)==2:
        p[0]=p[1]
    elif len(p)==3:
        symtab=get_current_symtab()
        name = p[2]+'('+p[1]._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible type for "+p[2]+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:[p[1]]})
    elif len(p)==4:
        name = p[1].value+"()"
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible type for "+p[1].value+" in line "+str(p.lineno(1))
            ERROR.append(err_msg)
            raise SyntaxError
        p[0] = Node("function call",i["return type"],children={i["name"]:None})       
    elif len(p)==5:
        if p[2]=='(':
            name = p[1].value+'('+','.join(p[3])+')'
            i = symtab.lookup(name)
            if i is None:
                err_msg = "Incompatible type for "+p[1].value+" in line "+str(p.lineno(1))
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
        symtab=get_current_symtab()
        name = '='+'('+p[1]._type.lower()+','+temp._type.lower()+')'
        i = symtab.lookup(name)
        if i is None:
            err_msg = "Incompatible types for = in line "+str(p.lineno(1))
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
    """declaration : declaration_specifiers ';'
    | declaration_specifiers init_declarator_list ';'"""
    p[0] = 

def p_declaration_specifiers(p):
    """declaration_specifiers : type_specifier
    | type_specifier declaration_specifiers"""
    p[0] = ("declaration_specifiers",) + tuple(p[-len(p)+1:])

def p_init_declarator_list(p):
    """init_declarator_list : init_declarator
    | init_declarator_list ',' init_declarator"""
    p[0] = ("init_declarator_list",) + tuple(p[-len(p)+1:])

def p_init_declarator(p):
    """init_declarator : declarator
    | declarator '=' initializer"""
    p[0] = ("init_declarator",) + tuple(p[-len(p)+1:])

def p_type_specifier(p):
    """type_specifier : VOID
    | CHAR
    | INT
    | BOOL"""
    p[0] = ("type_specifier",) + tuple(p[-len(p)+1:])


def p_specifier_qualifier_list(p):
    """specifier_qualifier_list : type_specifier specifier_qualifier_list
    | type_specifier"""
    p[0] = ("specifier_qualifier_list",) + tuple(p[-len(p)+1:])


def p_declarator(p):
    """declarator : pointer direct_declarator
    | direct_declarator"""
    p[0] = ("declarator",) + tuple(p[-len(p)+1:])

def p_direct_declarator(p):
    """direct_declarator : ID
    | '(' declarator ')'
    | direct_declarator '[' constant_expression ']'
    | direct_declarator '[' ']'
    | direct_declarator '(' parameter_list ')'
    | direct_declarator '(' identifier_list ')'
    | direct_declarator '(' ')'"""
    p[0] = ("direct_declarator",) + tuple(p[-len(p)+1:])

def p_pointer(p):
    """pointer : '*'
    | '*' pointer"""
    p[0] = ("pointer",) + tuple(p[-len(p)+1:])

def p_parameter_list(p):
    """parameter_list : parameter_declaration
    | parameter_list ',' parameter_declaration"""
    p[0] = ("parameter_list",) + tuple(p[-len(p)+1:])

def p_parameter_declaration(p):
    """parameter_declaration : declaration_specifiers declarator
    | declaration_specifiers abstract_declarator
    | declaration_specifiers"""
    p[0] = ("parameter_declaration",) + tuple(p[-len(p)+1:])

def p_identifier_list(p):
    """identifier_list : ID
    | identifier_list ',' ID"""
    p[0] = ("identifier_list",) + tuple(p[-len(p)+1:])

def p_type_name(p):
    """type_name : specifier_qualifier_list
    | specifier_qualifier_list abstract_declarator"""
    p[0] = ("type_name",) + tuple(p[-len(p)+1:])

def p_abstract_declarator(p):
    """abstract_declarator : pointer
    | direct_abstract_declarator
    | pointer direct_abstract_declarator"""
    p[0] = ("abstract_declarator",) + tuple(p[-len(p)+1:])

def p_direct_abstract_declarator(p):
    """direct_abstract_declarator : '(' abstract_declarator ')'
    | '[' ']'
    | '[' constant_expression ']'
    | direct_abstract_declarator '[' ']'
    | direct_abstract_declarator '[' constant_expression ']'
    | '(' ')'
    | '(' parameter_list ')'
    | direct_abstract_declarator '(' ')'
    | direct_abstract_declarator '(' parameter_list ')'"""
    p[0] = ("direct_abstract_declarator",) + tuple(p[-len(p)+1:])

def p_initializer(p):
    """initializer : assignment_expression
    | '{' initializer_list '}'
    | '{' initializer_list ',' '}'"""
    p[0] = ("initializer",) + tuple(p[-len(p)+1:])

def p_initializer_list(p):
    """initializer_list : initializer
    | initializer_list ',' initializer"""
    p[0] = ("initializer_list",) + tuple(p[-len(p)+1:])

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
    """compound_statement : '{' statement_list '}'
    | '{' declaration_list '}'
    | '{' declaration_list statement_list '}'"""
    if len(p)==4:
        p[0] = Node("statement","compound",value=p[2])
    else:
        p[0] = Node("statement","compound",value = p[2]+p[3])

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
        p[0] = Node("statement","expression",value=p[1])

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
    p[0] = Node("statement","jump",value=p[1])
    if len(p)==4:
        p[0].children = {"return":p[2]}

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
    """function_definition : declaration_specifiers declarator declaration_list compound_statement
    | declaration_specifiers declarator compound_statement
    | declarator declaration_list compound_statement
    | declarator compound_statement"""
    p[0] = ("function_definition",) + tuple(p[-len(p)+1:])
    
def p_input_statement(p):
    """input_statement : CIN IN id ';'"""
    p[0] = Node("statement","input",value=p[3])

def p_output_statement(p):
    """output_statement : COUT output_list ';'"""
    p[0]=Node("statement","output",value=p[2])
    
def p_output_list(p):
    """output_list : OUT primary_expression
    | output_list OUT primary_expression"""
    if len(p)==3:
        p[0]=[p[2]]
    else:
        p[0]=p[1]+[p[3]]
    
def p_error(p):
    global flag_for_error
    flag_for_error = 1

    if p is not None:
        print("error at line no:  %s :: %s" % ((p.lineno), (p.value)))
        parser.errok()
    else:
        print("Unexpected end of input")

parser = yacc.yacc()
#done
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

#done
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
            make_ast(result)
        else:
            for err in ERROR:
                print(err)   
