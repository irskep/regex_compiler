"""
Compile simple regular expressions to bytecode for hendersonvm.

This module implements a compiler for basic regular expressions. The grammar
implementation is based on the one described in the `1997 Single UNIX
Specification <http://opengroup.org/onlinepubs/007908775/xbd/re.html>`_.

The allowed operators are ?, +, *, (), and escape sequences for those
characters. No other escape sequences are supported.
"""

import logging
import subprocess

logging.basicConfig()

import instructions
import lexer
import parser
import visualize


log = logging.getLogger(__name__)


def show(s, reduced=True, out_path="AST", make_pdf=True,
              print_tokens=False, print_instructions=False):
    """

    Generates a graphviz diagram of the AST for the given path. Since this is
    mostly debug functionality, there are also options to print various
    significant values.

    :param s: The regular expression to parse
    :param reduced: If True, includes only productions used for generating code
                    in the diagram. If False, includes all productions in the
                    diagram. Defaults to False.
    :param out_path: Destination for the graphviz document without any
                     extension
    :param make_pdf: Also create a PDF using the local graphviz installation
    :param print_tokens: Print the tokens as seen by the lexer to the console
    :param print_instructions: Pretty-print the resulting list of instructions
                               to the console
    """
    if print_tokens:
        log.info('Tokens:')
        lexer.lexer.input(s)
        for tok in iter(lexer.lexer.token, None):
            log.info(repr(tok.type), repr(tok.value))
    root = parser.parse(s, (not reduced))

    visualize.ast_dot(root, "%s.dot" % out_path)
    log.info("Graphviz written to %s.dot" % out_path)
    if make_pdf:
        try:
            subprocess.call(["dot", "-Tpdf",  "%s.dot" % out_path,
                             "-o",  "%s.pdf" % out_path])
            log.info("PDF written to %s.pdf" % out_path)
        except OSError:
            log.info("PDF could not be written, Graphviz does not appear to be"
                     " installed")

    instr_list = root.generate_instructions()
    instr_list.append(instructions.Instruction('match'))
    # Print instructions after the AST is drawn in case instruction printing fails
    program = instructions.serialize(instr_list)
    if print_instructions:
        log.info("Instructions for VM:")
        instructions.prettyprint_program(program)

    return program


def parse(s):
    """
    Converts a regular expression into bytecode for the VM

    :param s: A regular expression
    :return: A list of opcode tuples in the form `[(opcode, arg1, arg2)]`
    """
    instr_list = parser.parse(s).generate_instructions()
    instr_list.append(instructions.Instruction('match'))
    return instructions.serialize(instr_list)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        expr = sys.argv[1]
        show(expr, print_instructions=True, print_tokens=True)
    else:
        print >> sys.stderr, "Usage: python __init__.py [regex]"

