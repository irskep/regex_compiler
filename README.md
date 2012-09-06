Rajax: Regex Bytecode Compiler
==============================

This module turns regular expressions into bytecode for execution on the
virtual machine invented by Ken Thompson and [described by Russ
Cox](http://swtch.com/~rsc/regexp/). It also produces a
[Graphviz](http://www.graphviz.org/) representation of the abstract syntax tree
(with some nodes removed).

Some of the VM instructions (`NCHAR`, `WILD`) are not documented by Cox.
`NCHAR` means "match anything but this" and `WILD` is the wildcard.

Usage
-----

    python -m rajax [regex]

Install
-------

    pip install -e git+https://github.com/cwru-compilers/regex_compiler.git#egg=rajax

Example
-------

    python -m rajax ab[\D8]+
    
    Tokens:
    'ORD_CHAR' 'a'
    'ORD_CHAR' 'b'
    'LBRACK' '['
    'ES_SPECIAL' 'D'
    'ORD_CHAR' '8'
    'RBRACK' ']'
    'PLUS' '+'
    -------
    Graphviz written to AST.dot
    PDF written to AST.pdf
    -------
    Instructions for VM:
     0: char    a ZERO
     1: char    b ZERO
     2: split   3   5
     3: split   4   7
     4: jmp     9
     5: char    : INF
     6: jmp    10
     7: char  ZERO   /
     8: jmp    10
     9: char    8 ZERO
    10: split   2  11
    11: match

`AST.dot` will look like this:

    digraph AST {
        node [shape=box];
        {
            rank=same; 
            1 [label="re_expr_concat: ", style=filled, fillcolor="#eeeeee"];
        }
        {
            rank=same; 
            2 [label="re_expr_concat: ", style=filled, fillcolor="#eeeeee"];
            5 [label="simple_re_dup: +", style=filled, fillcolor="#ccffcc"];
        }
        {
            rank=same; 
            3 [label="nondup_re_char: a", style=filled, fillcolor="#ffffcc"];
            4 [label="nondup_re_char: b", style=filled, fillcolor="#ffffcc"];
            6 [label="brack_expr_matching_list: ", style=filled, fillcolor="#ffffff"];
        }
        {
            rank=same; 
            7 [label="follow_list_multi: ", style=filled, fillcolor="#cccccc"];
        }
        {
            rank=same; 
            8 [label="char_class: D", style=filled, fillcolor="#ffcccc"];
            9 [label="end_range_char: 8", style=filled, fillcolor="#ccccff"];
        }
        1 -> 2;
        1 -> 5;
        2 -> 3;
        2 -> 4;
        5 -> 6;
        6 -> 7;
        7 -> 8;
        7 -> 9;
    }
