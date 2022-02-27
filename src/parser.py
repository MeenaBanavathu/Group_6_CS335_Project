import scanner as lex
import ply.yacc as yacc

token,literal = lex.scanner.tokens,lex.scanner.literals

def p_func_def(p):
    '''function : type STRING '(' args ')' block '''
    p[0] = {"type":'FUNC',"ret_type":p[1],"name":p[2],"args":p[4],"block":p[6]}

def p_func_declare(p):
    '''function : type STRING '(' args ')' ';' '''
    p[0] = {"type":'FUNC_DECLARE',"ret_type":p[1],"name":p[2],"args":p[4]}
    
def p_struct(p):
    '''struct : STRUCT STRING '{' declare_var '}' ';' '''
    p[0] = {"type":'STRUCT',"name":p[2],"declarations":p[4]}

def p_class(p):
    
    
def p_if(p):
    '''if : IF '(' condition ')' block'''
    p[0] = {"type":"IF", "condition":p[3], "block":p[5]}

def p_ifelse(p):
    '''if_else : IF '(' condition ')' block ELSE block '''
    p[0] = {"type":'IF_ELSE', "condition":p[3],"if_block":p[5],"else_block":p[7]}
    
def p_for(p):
    '''for : FOR '(' init ';' condition ';' modification ')' block '''
    p[0] = {"type":'FOR',"init":p[3],"condition":p[5],"update":p[7],"block":p[9]}

def p_while(p):
    '''while : WHILE '(' condition ')' block '''
    p[0] = {"type":'WHILE',"condition":p[3],"block":p[5]}

def p_block(p):
    '''block : '{' list_statements '}' '''
    
def p_statements(p):
    '''list_statements : list_statements statement ';'
                        | statement ';' '''
    
def p_array1(p):
    '''array : type STRING '[' INTEGER ']' ';' '''
    
def p_array2(p):
    '''array : type STRING '[' INTEGER ']' '=' '{' list '}' ';' '''
def p_assign(p):
    '''assign : ID '=' expr ';' '''
    p[0] = ('=',p[1],p[3])
def p_input(p):
    '''input : CIN ID ';' '''
    p[0] = {"type":'INPUT',"inp":p[2]}

def p_output(p):
    '''output : COUT out ';' '''
    p[0] = ('OUTPUT',p[2])
def p_out(p):
    '''out : OUTPUT var out
            | OUTPUT ID out
            | OUTPUT ID
            | OUTPUT var'''
    p[0] = ('out',)+tuple(p[-len(p) + 1 :])

def p_expr(p):
    '''expr : expr '+' term
             | expr '-' term
             | term'''
    
    p[0] = ('expr',)+tuple(p[-len(p) + 1 :])
def p_term(p):
    '''term : term '*' factor
             | term '/' factor
             | term '%' factor
             | factor'''
    p[0] = ('term',)+tuple(p[-len(p) + 1 :])
def p_factor(p):
    '''factor : INT
              | ID'''
    p[0]=(p[1],)
def p_compare(p):
    '''compare : expr '&' expr 
                | expr '|' expr 
                | expr '^' expr 
                | expr '>' expr 
                | expr '<' expr
                | expr LE expr
                | expr GE expr
                | expr EQUAL expr
                | expr NE expr'''
    p[0]=(p[2],p[1],p[3])
    
