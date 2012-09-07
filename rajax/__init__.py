"""
Compile simple regular expressions to bytecode for hendersonvm.

This module implements a compiler for basic regular expressions. The grammar
implementation is based on the one described in the `1997 Single UNIX
Specification <http://opengroup.org/onlinepubs/007908775/xbd/re.html>`_.

The allowed operators are ?, +, *, (), and escape sequences for those
characters. No other escape sequences are supported.
"""

import instructions
import lexer
import parser
import visualize

__version__ = 0.
