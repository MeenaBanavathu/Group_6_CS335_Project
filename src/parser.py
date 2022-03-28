import sys
import os
import scanner
import ply.yacc as yacc


tokens = scanner.scanner.tokens
literals = scanner.scanner.literals
flag_for_error = 0

start = "translation_unit"

def p_primary_expression(p):
    """primary_expression : ID
    | INTEGER
    | STRING
    | TRUE
    | FALSE
    | CHARACTER
    | '(' expression ')' """
    p[0] = ("primary_expression",) + tuple(p[-len(p)+1:])

def p_postfix_expression(p):
    """postfix_expression : primary_expression
    | postfix_expression '[' expression ']'
    | postfix_expression '(' ')'
    | postfix_expression '(' argument_expression_list ')'
    | postfix_expression '.' ID
    | postfix_expression PTR ID
    | postfix_expression INC
    | postfix_expression DEC"""
    p[0] = ("postfix_expression",) + tuple(p[-len(p)+1:])

def p_argument_expression_list(p):
    """argument_expression_list : assignment_expression
    | argument_expression_list ',' assignment_expression"""
    p[0] = ("argument_expression_list",) + tuple(p[-len(p)+1:])

def p_unary_expression(p):
    """unary_expression : postfix_expression
    | INC unary_expression
    | DEC unary_expression
    | unary_operator cast_expression"""
    p[0] = ("unary_expression",) + tuple(p[-len(p)+1:])

def p_unary_operator(p):
    """unary_operator : '&'
    | '*'
    | '+'
    | '-'
    | '~'
    | '!'"""
    p[0] = ("unary_operator",) + tuple(p[-len(p)+1:])

def p_cast_expression(p):
    """cast_expression : unary_expression
    | '(' type_name ')' cast_expression"""
    p[0] = ("cast_expression",) + tuple(p[-len(p)+1:])

def p_multiplicative_expression(p):
    """multiplicative_expression : cast_expression
    | multiplicative_expression '*' cast_expression
    | multiplicative_expression '/' cast_expression
    | multiplicative_expression '%' cast_expression"""
    p[0] = ("multiplicative_expression",) + tuple(p[-len(p)+1:])

def p_additive_expression(p):
    """additive_expression : multiplicative_expression
    | additive_expression '+' multiplicative_expression
    | additive_expression '-' multiplicative_expression"""
    p[0] = ("additive_expression",) + tuple(p[-len(p)+1:])

def p_relational_expression(p):
    """relational_expression : additive_expression
    | relational_expression '<' additive_expression
    | relational_expression '>' additive_expression
    | relational_expression LE additive_expression
    | relational_expression GE additive_expression"""
    p[0] = ("relational_expression",) + tuple(p[-len(p)+1:])

def p_equality_expression(p):
    """equality_expression : relational_expression
    | equality_expression EQUAL relational_expression
    | equality_expression NE relational_expression"""
    p[0] = ("equality_expression",) + tuple(p[-len(p)+1:])

def p_and_expression(p):
    """and_expression : equality_expression
    | and_expression '&' equality_expression"""
    p[0] = ("and_expression",) + tuple(p[-len(p)+1:])

def p_exclusive_or_expression(p):
    """exclusive_or_expression : and_expression
    | exclusive_or_expression '^' and_expression"""
    p[0] = ("exclusive_or_expression",) + tuple(p[-len(p)+1:])

def p_inclusive_or_expression(p):
    """inclusive_or_expression : exclusive_or_expression
    | inclusive_or_expression '|' exclusive_or_expression"""
    p[0] = ("inclusive_or_expression",) + tuple(p[-len(p)+1:])

def p_logical_and_expression(p):
    """logical_and_expression : inclusive_or_expression
    | logical_and_expression AND inclusive_or_expression"""
    p[0] = ("logical_and_expression",) + tuple(p[-len(p)+1:])

def p_logical_or_expression(p):
    """logical_or_expression : logical_and_expression
    | logical_or_expression OR logical_and_expression"""
    p[0] = ("logical_or_expression",) + tuple(p[-len(p)+1:])

def p_conditional_expression(p):
    """conditional_expression : logical_or_expression
    | logical_or_expression '?' expression ':' conditional_expression"""
    p[0] = ("conditional_expression",) + tuple(p[-len(p)+1:])

def p_assignment_expression(p):
    """assignment_expression : conditional_expression
    | unary_expression assignment_operator assignment_expression"""
    p[0] = ("assignment_expression",) + tuple(p[-len(p)+1:])

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
    p[0] = ("assignment_operator",) + tuple(p[-len(p)+1:])

def p_expression(p):
    """expression : assignment_expression
    | expression ',' assignment_expression"""
    p[0] = ("expression",) + tuple(p[-len(p)+1:])

def p_constant_expression(p):
    """constant_expression : conditional_expression"""
    p[0] = ("constant_expression",) + tuple(p[-len(p)+1:])

def p_declaration(p):
    """declaration : declaration_specifiers ';'
    | declaration_specifiers init_declarator_list ';'"""
    p[0] = ("declaration",) + tuple(p[-len(p)+1:])

def p_declaration_specifiers(p):
    """declaration_specifiers : 
    | type_specifier
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
    | BOOL
    | struct_specifier
    | class_definition"""
    p[0] = ("type_specifier",) + tuple(p[-len(p)+1:])

def p_class_definition(p):
    """class_definition : CLASS ID '{' class_member_list '}'"""
    p[0] = ("class_definition",) + tuple(p[-len(p)+1:])

def p_class_member_list(p):
    """class_member_list : class_member
    | class_member_list class_member"""
    p[0] = ("class_member_list",) + tuple(p[-len(p)+1:])

def p_class_member(p):
    """class_member : function_definition
    | declaration"""
    p[0] = ("class_member",) + tuple(p[-len(p)+1:])

def p_struct_specifier(p):
    """struct_specifier : STRUCT ID '{' struct_declaration_list '}'"""
    p[0] = ("struct_specifier",) + tuple(p[-len(p)+1:])

def p_struct_declaration_list(p):
    """struct_declaration_list : struct_declaration
    | struct_declaration_list struct_declaration"""
    p[0] = ("struct_declaration_list",) + tuple(p[-len(p)+1:])

def p_struct_declaration(p):
    """struct_declaration : specifier_qualifier_list struct_declarator_list ';' """
    p[0] = ("struct_declaration",) + tuple(p[-len(p)+1:])

def p_specifier_qualifier_list(p):
    """specifier_qualifier_list : type_specifier specifier_qualifier_list
    | type_specifier"""
    p[0] = ("specifier_qualifier_list",) + tuple(p[-len(p)+1:])

def p_struct_declarator_list(p):
    """struct_declarator_list : struct_declarator
    | struct_declarator_list ',' struct_declarator"""
    p[0] = ("struct_declarator_list",) + tuple(p[-len(p)+1:])

def p_struct_declarator(p):
    """struct_declarator : declarator
    | ':' constant_expression
    | declarator ':' constant_expression"""
    p[0] = ("struct_declarator",) + tuple(p[-len(p)+1:])

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
    p[0] = ("statement",) + tuple(p[-len(p)+1:])

def p_compound_statement(p):
    """compound_statement : '{' statement_list '}'
    | '{' declaration_list '}'
    | '{' declaration_list statement_list '}'"""
    p[0] = ("compound_statement",) + tuple(p[-len(p)+1:])

def p_declaration_list(p):
    """declaration_list : declaration
    | declaration_list declaration"""
    p[0] = ("declaration_list",) + tuple(p[-len(p)+1:])

def p_statement_list(p):
    """statement_list : statement
    | statement_list statement"""
    p[0] = ("statement_list",) + tuple(p[-len(p)+1:])

def p_expression_statement(p):
    """expression_statement : ';'
    | expression ';'"""
    p[0] = ("expression_statement",) + tuple(p[-len(p)+1:])

def p_selection_statement(p):
    """selection_statement : IF '(' expression ')' statement
    | IF '(' expression ')' statement ELSE statement"""
    p[0] = ("selection_statement",) + tuple(p[-len(p)+1:])

def p_iteration_statement(p):
    """iteration_statement : WHILE '(' expression ')' statement
    | FOR '(' expression_statement expression_statement expression ')' statement"""
    p[0] = ("iteration_statement",) + tuple(p[-len(p)+1:])

def p_jump_statement(p):
    """jump_statement : CONTINUE ';'
    | BREAK ';'
    | RETURN ';'
    | RETURN expression ';'"""
    p[0] = ("jump_statement",) + tuple(p[-len(p)+1:])

def p_translation_unit(p):
    """translation_unit : external_declaration
    | translation_unit external_declaration"""
    p[0] = ("translation_unit",) + tuple(p[-len(p)+1:])

def p_external_declaration(p):
    """external_declaration : function_definition
    | declaration"""
    p[0] = ("external_declaration",) + tuple(p[-len(p)+1:])

def p_function_definition(p):
    """function_definition : declaration_specifiers declarator declaration_list compound_statement
    | declaration_specifiers declarator compound_statement
    | declarator declaration_list compound_statement
    | declarator compound_statement"""
    p[0] = ("function_definition",) + tuple(p[-len(p)+1:])
    
def p_input_statement(p):
    """input_statement : CIN IN ID ';'"""
    p[0] = ("input_statement",) + tuple(p[-len(p)+1:])

def p_output_statement(p):
    """output_statement : COUT output_list ';'"""
    p[0] = ("output_statement",) + tuple(p[-len(p)+1:])
    
def p_output_list(p):
    """output_list : OUT primary_expression
    | output_list OUT primary_expression"""
    p[0] = ("output_list",) + tuple(p[-len(p)+1:])
    
def p_error(p):
    global flag_for_error
    flag_for_error = 1

    if p is not None:
        print("error at line no:  %s :: %s" % ((p.lineno), (p.value)))
        parser.errok()
    else:
        print("Unexpected end of input")
parser = yacc.yacc()
if __name__ == "__main__":
    if(len(sys.argv) == 2):
        file = sys.argv[1]
        fl = open(file,'r')
        inp = fl.read()
        result = parser.parser(inp)
print(result)
