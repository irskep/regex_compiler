Regex Bytecode Compiler
=======================

This module turns regular expressions into bytecode for execution on the virtual machine invented by Ken Thomson and (described by Russ Cox)[http://swtch.com/~rsc/regexp/]. It also produces a [Graphviz](http://www.graphviz.org/) representation of the abstract syntax tree (with some nodes removed).

Dire Warning
------------
This is intended to be *example code only*. It is part of the unreleased [SourceQL project](http://timunionsteve.posterous.com/mercurial-ate-our-breakfast-but-we-dont-mind). The docstrings are written in [epydoc](http://epydoc.sourceforge.net/) format which went out of style years ago.

Some of the VM instructions (`NCHAR`, `WILD`) are not documented by Cox. `NCHAR` means "match anything but this" and `WILD` is the wildcard.

Usage
-----

    python __init__.py [regex]

Example
-------

    python __init__.py ab[\D8]+
    
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
