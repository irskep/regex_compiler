"""
Parser using a grammar mostly derived from the U{1997 Single UNIX Specification<http://opengroup.org/onlinepubs/007908775/xbd/re.html>}
"""

# Steve Johnson, January 2009
# steve.johnson.public@gmail.com

import ply.yacc as yacc

from lexer import *
from ast import *
from instructions import *
from const import *

# (some\\one)?and *(my)+ d|og

# Print debug info during parsing
debug = False

# If True, AST will contain *all* productions. Otherwise it is progressively collapsed.
full_graph = False

def parse(s, fg=False):
    """
    Parse a string into an AST
    
    @param s: A regular expression
    @param fg: If True, an AST node is generated for every production.
    
    @return: Root of the AST
    @rtype: L{ASTNode}
    """
    global full_graph
    full_graph = fg
    return parser.parse(s)

precedence = (
    ('left', 'STAR', 'PLUS', 'QMARK'),
)

# ========================
# = Basic Regex Patterns =
# ========================
def p_regex(p):
    """
    regex :             re_expr
    regex : regex PIPE  re_expr
    """
    if len(p) == 2:
        if full_graph:
            p[0] = RegexNode("plain", [p[1]])
        else:
            p[0] = p[1]
    elif len(p) == 4:
        p[0] = RegexNode("alt", [p[1], p[3]])
    if debug: print str(p[0]), p[0].children

def p_re_expr(p):
    """
    re_expr :               simple_re
    re_expr :   re_expr     simple_re
    """
    if len(p) == 2:
        if full_graph:
            p[0] = ASTNode("re_expr", "plain", [p[1]])
        else:
            p[0] = p[1]
    elif len(p) == 3:
        p[0] = ASTNode("re_expr", "concat", [p[1], p[2]])
    if debug: print str(p[0]), p[0].children

def p_simple_re(p):
    """
    simple_re : nondup_re
    simple_re : nondup_re   dup_symb
    """
    if len(p) == 2:
        if full_graph:
            p[0] = SimpleReNode("plain", [p[1]])
        else:
            p[0] = p[1]
    elif len(p) == 3:
        if full_graph:
            p[0] = SimpleReNode("dup", [p[1], p[2]], data=p[2].data)
        else:
            p[0] = SimpleReNode("dup", [p[1]], data=p[2].data)
    if debug: print str(p[0]), p[0].children

def p_dup_symb(p):
    """
    dup_symb :  STAR
    dup_symb :  PLUS
    dup_symb :  QMARK
    """
    p[0] = ASTNode("dup_symb", data=p[1])
    if debug: print str(p[0]), p[0].children

def p_nondup_re(p):
    """
    nondup_re : one_char
    nondup_re : LPAREN      regex       RPAREN
    """
    if len(p) == 2:
        if p[1].node_type == 'brack_expr' or p[1].subtype == 'brack_expr':
            if full_graph:
                p[0] = ASTNode("nondup_re", "brack_expr", [p[1]])
            else:
                p[0] = p[1]
        else:
            if full_graph:
                p[0] = NonDupReNode("char", children=[p[1]], data=p[1].data)
            else:
                p[0] = NonDupReNode("char", data=p[1].data)
    elif len(p) == 4:
        if full_graph:
            p[0] = NonDupReNode("group", [p[2]], data=p[2].data)
        else:
            p[0] = p[2]
    if debug: print str(p[0]), p[0].children

def p_one_char(p):
    """
    one_char :  ORD_CHAR
    one_char :  ES_NORMAL
    one_char :  DOT
    one_char :  DASH
    one_char :  brack_expr
    one_char :  escaped_char
    """
    if isinstance(p[1], ASTNode):
        if p[1].node_type == 'brack_expr':
            if full_graph:
                p[0] = ASTNode("one_char", "brack_expr", [p[1]])
            else:
                p[0] = p[1]
        else:
            p[0] = ASTNode("one_char", "escape", [p[1]], data=p[1].data)
    else:
        if p[1] == '.':
            p[0] = ASTNode("one_char", "wildcard", data=WILDCARD)
        else:
            p[0] = ASTNode("one_char", "normal", data=p[1])
    if debug: print str(p[0]), p[0].children

def p_escaped_char(p):
    """
    escaped_char :  ES_CHAR
    """
    p[0] = ASTNode("escaped_char", p[1], data=str_esc_seq[p[1]])

# =======================
# = Bracket Expressions =
# =======================
def p_brack_expr(p):
    """
    brack_expr :    LBRACK  matching_list       RBRACK
    brack_expr :    LBRACK  nonmatching_list    RBRACK
    brack_expr :    special_escape
    """
    if len(p) == 4:
        if full_graph:
            p[0] = BrackExprListNode(p[2].node_type, [p[2]])
        else:
            p[0] = BrackExprListNode(p[2].node_type, p[2].children)
    elif len(p) == 2:
        if char_classes_m.has_key(p[1].data):
            p[0] = BrackExprListNode("matching_list", [p[1]])
        elif char_classes_nm.has_key(p[1].data):
            p[0] = BrackExprListNode("nonmatching_list", [p[1]])
        else:
            raise Exception("Bad escape sequence: %s" % p[1].data)
    if debug: print str(p[0]), p[0].children

def p_matching_list(p):
    """
    matching_list : bracket_list
    """
    p[0] = ASTNode("matching_list", children=[p[1]])
    if debug: print str(p[0]), p[0].children

def p_nonmatching_list(p):
    """
    nonmatching_list : CARAT    bracket_list
    """
    p[0] = ASTNode("nonmatching_list", children=[p[2]])
    if debug: print str(p[0]), p[0].children

def p_bracket_list(p):
    """
    bracket_list :  follow_list
    bracket_list :  follow_list DASH
    """
    if len(p) == 2:
        if full_graph:
            p[0] = ASTNode("bracket_list", "plain", children=[p[1]])
        else:
            p[0] = p[1]
    elif len(p) == 3:
        if full_graph:
            p[0] = ASTNode("bracket_list", "range", children=[p[1]])
        else:
            p[0] = p[1]
    if debug: print str(p[0]), p[0].children

def p_follow_list(p):
    """
    follow_list :               expr_term
    follow_list :   follow_list expr_term
    """
    if len(p) == 2:
        if full_graph:
            p[0] = ASTNode("follow_list", "plain", children=[p[1]])
        else:
            p[0] = p[1]
    elif len(p) == 3:
        p[0] = ASTNode("follow_list", "multi", children=[p[1], p[2]])
    if debug: print str(p[0]), p[0].children

def p_expr_term(p):
    """
    expr_term : single_expr
    expr_term : range_expr
    expr_term : special_escape
    """
    if full_graph:
        p[0] = ASTNode("expr_term", children=[p[1]])
    else:
        p[0] = p[1]
    if debug: print str(p[0]), p[0].children

def p_single_expr(p):
    """
    single_expr :   end_range
    """
    if full_graph:
        p[0] = ASTNode("single_expr", children=[p[1]])
    else:
        p[0] = p[1]
    if debug: print str(p[0]), p[0].children

def p_range_expr(p):
    """
    range_expr :    start_range     end_range
    range_expr :    start_range     DASH
    """
    if isinstance(p[2], ASTNode):
        p[0] = RangeExprNode(children=[p[1], p[2]])
    else:
        p[0] = RangeExprNode(children=[p[1], EndRangeNode('char', data=p[2])])
    if debug: print str(p[0]), p[0].children

def p_start_range(p):
    """
    start_range :   end_range   DASH
    """
    if isinstance(p[1], ASTNode):
        if full_graph:
            p[0] = ASTNode("start_range", children=[p[1]], data=p[1].data)
        else:
            p[0] = p[1]
    else:
        p[0] = ASTNode("start_range", data=p[1])
    if debug: print str(p[0]), p[0].children

def p_end_range(p):
    """
    end_range : ORD_CHAR
    end_range : ES_NORMAL
    end_range : escaped_char
    """
    if isinstance(p[1], ASTNode):
        if full_graph:
            p[0] = EndRangeNode('char', children=[p[1]], data=p[1].data)
        else:
            p[0] = EndRangeNode('char', data=p[1].data)
    else:
        p[0] = EndRangeNode('char', data=p[1])

def p_special_escape(p):
    """
    special_escape :    ES_SPECIAL
    """
    p[0] = CharClassNode(p[1])

def p_error(p):
    raise TypeError("unknown text at %r" % (p.value,))

parser = yacc.yacc(debug=0)

