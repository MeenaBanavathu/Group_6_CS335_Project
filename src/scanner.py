import sys
import ply.lex as lex
from ply.lex import TOKEN
from tabulate import tabulate

keywords = [
    'break','char','continue','else','for','if','int','return','struct',
    'void','while','bool','false','class','true','cin','cout'
]
reserved = {i:i.upper() for i in keywords}

class LexerCPP(object):
    tokens = [
        'ID','INTEGER','STRING','CHARACTER','PTR','LE','GE','EQUAL','NE','AND','OR','IN','OUT',
        'ADD_EQ','SUB_EQ','MUL_EQ','DIV_EQ','MOD_EQ','AND_EQ','XOR_EQ','OR_EQ','INC','DEC'
    ]+list(reserved.values())
    literals = ['(',')','[',']','{','}','.','+','-','*','/','%','!','<','>','&','|','^','=',',',';',':','?']
    identifier = r'[_a-zA-Z][_a-zA-Z0-9]*'
    hexadec = r'(0[xX][0-9a-fA-F]+)'
    digit = r'([0-9]+)'
    octdec = r'(0[0-7]+)'
    binary = r'(0[bB][01]+)'
    integer = r'('+hexadec+'|'+digit+'|'+octdec+'|'+binary+')'
    charac = r"\'.\'"
    newline = r'\n+'
    string = r'\".*\"'

    t_ignore_WS = r'[ \f\v\t]+'
    t_PTR = r'->'
    t_LE = r'<='
    t_GE = r'>='
    t_EQUAL = r'=='
    t_NE = r'!='
    t_AND = r'&&'
    t_OR = r'\|\|'
    
    t_ADD_EQ = r"\+="
    t_SUB_EQ = r"-="
    t_MUL_EQ = r"\*="
    t_DIV_EQ = r"/="
    t_MOD_EQ = r"%="
    t_AND_EQ = r"&="
    t_XOR_EQ = r"^="
    t_OR_EQ = r"\|="
    
    t_IN = r">>"
    t_OUT = r"<<"

    t_INC = r"\+\+"
    t_DEC = r"--"
    
    @TOKEN(identifier)
    def t_ID(self,t):
        t.type = reserved.get(t.value,'ID')
        return t

    @TOKEN(integer)
    def t_INTEGER(self,t):
        t.value = int(t.value)
        return t

    @TOKEN(charac)
    def t_CHARACTER(self,t):
        return t

    @TOKEN(string)
    def t_STRING(self,t):
        return t

    def t_newline(self,t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_comment(self,t):
        r'((//.*)|(/\*(.|\n)*?\*/)\n)'
        t.lexer.lineno += t.value.count('\n')
        
    def t_error(self,t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)
    
    def build(self):
        self.lexer = lex.lex(module=self)
    
    def test(self,inp):
        self.lexer.input(inp)
        lst = []
        while True:
            tok = self.lexer.token()
            if not tok: 
                break
            lst.append([tok.type, tok.value, tok.lineno, tok.lexpos])
        print(tabulate(lst, headers=['Token', 'Lexeme','Line#','Column#']))

scanner = LexerCPP()
scanner.build()
if __name__ == "__main__":
    if(len(sys.argv) == 2):
        file = sys.argv[1]
        fl = open(file,'r')
        inp = fl.read()
        scanner.test(inp)
    else:
        lex.runmain(scanner.lexer)
