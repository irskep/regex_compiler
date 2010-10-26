"""
A bare-bones lexer. Most of the heavy lifting is done by the parser due to limitations with ply's lexer with regards to character classes.
"""

# Steve Johnson, January 2009
# steve.johnson.public@gmail.com

# ()|+*?[^]

import ply.lex as lex
import const

states = (
  ('brackexpr','exclusive'),   # bracket expression
  ('escseq','exclusive'),      # escape sequence
)

# ===========
# = INITIAL =
# ===========
weirdchars = r"\\\*\+\?\(\)\|\[\]\^"

tokens = (
    "ORD_CHAR",
    "LPAREN", "RPAREN",
    "LBRACK", "RBRACK",
    "BACKSLASH",
    "CARAT",
    "DASH",
    "STAR",
    "PLUS",
    "QMARK",
    "DOT",
    "PIPE",
    "ES_NORMAL",
    "ES_CHAR",
    "ES_SPECIAL",
)

def t_LBRACK(t):
    r"\["
    t.lexer.first = True
    t.lexer.begin('brackexpr')
    return t

def t_BACKSLASH(t):
    r"\\"
    t.lexer.in_brack_expr = False
    t.lexer.push_state('escseq')
    
    # TRICKY THING: Since we are cloning the lexer, the next token is going to
    # cause a state to be popped off of the stach which is *shared by both*.
    # So I'll just push it twice.
    t.lexer.push_state('escseq')
    
    scout = t.lexer.clone()
    scout.plunk = 'a'
    t.lexer.plunk = 'b'
    future_token = scout.token()
    del scout   # because I'm paranoid
    if future_token.value == '-':
        t.type = "ORD_CHAR"
        return t

t_ORD_CHAR = r"[^%s]" % weirdchars
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_CARAT = r"\^"
t_STAR = r"\*"
t_PLUS = r"\+"
t_QMARK = r"\?"
t_DOT = r"\."
t_PIPE = r"\|"

# =============
# = brackexpr =
# =============

def t_brackexpr_RBRACK(t):
    r"\]"
    if t.lexer.first == True:
        t.type = "ORD_CHAR"
        t.first = False
    else:
        t.lexer.begin('INITIAL')
    return t

def t_brackexpr_ORD_CHAR(t):
    r"[^^\]\\-]"
    t.lexer.first = False
    return t

def t_brackexpr_CARAT(t):
    r"\^"
    if not t.lexer.first:
        t.type = "ORD_CHAR"
    return t

def t_brackexpr_DASH(t):
    r"-"
    if t.lexer.first:
        t.type = "ORD_CHAR"
        t.lexer.first = False
    return t

def t_brackexpr_BACKSLASH(t):
    r"\\"
    t.lexer.push_state('escseq')
    t.lexer.in_brack_expr = True

# ==========
# = escseq =
# ==========

def t_escseq_ES_NORMAL(t):
    r"[\\\*\+\?\(\)\|\[\]\^-]"
    if not t.lexer.in_brack_expr and t.value == '-':
        t.type = "ORD_CHAR"
    t.lexer.first = False
    t.lexer.pop_state()
    return t

def t_escseq_ES_CHAR(t):
    r"[tnrfv]"
    # This token should get more sophisticated. And more correct. As of now,
    # the magic happens in parser.p_escaped_char.
    t.lexer.first = False
    t.lexer.pop_state()
    return t

def t_escseq_ES_SPECIAL(t):
    r"[wWdD]"
    t.lexer.first = False
    t.lexer.pop_state()
    return t

def t_error(t):
    raise TypeError("Error in text '%s'" % (t.value,))

def t_brackexpr_error(t):
    raise TypeError("Error in bracket expression: '%s'" % (t.value,))

def t_escseq_error(t):
    raise TypeError("Bad escape sequence: '%s'" % (t.value[0],))

lexer = lex.lex()

if __name__ == '__main__':
    lex.input(r"i [at*e] \nsom\\e snow [^]today]")
    for tok in iter(lex.token, None):
        print repr(tok.type), repr(tok.value)