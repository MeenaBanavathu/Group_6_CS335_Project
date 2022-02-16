import sys
import ply.lex as lex
from ply.lex import TOKEN
from tabulate import tabulate

keywords = ['auto','break','case','char','const','continue','default','do','else','enum','extern',
            'for','goto','if','int','register','return','signed','sizeof','static','cin','cout'
            'struct','switch','typedef','union','unsigned','void','volatile','while','asm','dynamic_cast',
            'namespace','reinterpret_cast','bool','explicit','new','static_cast','false','catch','operator',
            'template','friend','private','class','this','inline','public','throw','const_cast','delete',
            'mutable''protected','true','try','typeid','typename','using','virtual','wchar_t']
reserved = {i:i.upper() for i in keywords}

class LexerCPP(object):
    tokens = ['ID','INTEGER','STRING','CHARACTER','PTR','LE','GE','EQUAL','INPUT','OUTPUT','NE','AND','OR']+list(reserved.values())
    literals = ['(',')','[',']','{','}','.','+','-','*','/','%','!','<','>','&','|','^','=',',',';']
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
    t_INPUT = r'>>'
    t_OUTPUT = r'<<'
    t_AND = r'&&'
    t_OR = r'\|\|'
    
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
