"""
Compile simple regular expressions to bytecode for hendersonvm.

This module implements a compiler for basic regular expressions. The grammar
implementation is based on the one described in the `1997 Single UNIX
Specification <http://opengroup.org/onlinepubs/007908775/xbd/re.html>`_.

The allowed operators are ?, +, *, (), and escape sequences for those
characters. No other escape sequences are supported.
"""

import sys
import logging
import subprocess
import json
from getopt import getopt, GetoptError

logging.basicConfig()
log = logging.getLogger(__name__)

import instructions
import lexer
import parser
import visualize
from rajax.const import opcode_to_cmd


error_codes = {
    'usage':1,
    'file_not_found':2,
    'option':3,
    'args':4,
    'version':5,
    'database':6
}

usage_message = \
'''usage: python -m rajax [flags] <regex>'''

extended_message = \
    '''
Compile a regex into NFA instructions.

Options

    -h, help                            print this message
    -v, version                         print the version
    -j, json                            emit json instead of text
'''


def _log(*msgs):
    for msg in msgs:
        print >>sys.stderr, msg,
    print >>sys.stderr
    sys.stderr.flush()

def version():
    '''Print version and exits'''
    _log('version :', __version__)
    sys.exit(error_codes['version'])

def usage(code=None):
    ''' Prints the usage and exits with an error code specified by code. If code
    is not given it exits with error_codes['usage']'''
    _log(usage_message)
    if code is None:
        _log(extended_message)
        code = error_codes['usage']
    sys.exit(code)

def show(s, reduced=True, out_path="AST", make_pdf=True,
              print_tokens=False, print_json=False):
    """

    Generates a graphviz diagram of the AST for the given path. Since this is
    mostly debug functionality, there are also options to print various
    significant values.

    :param s: The regular expression to parse
    :param reduced: If True, includes only productions used for generating code
                    in the diagram. If False, includes all productions in the
                    diagram. Defaults to True.
    :param out_path: Destination for the graphviz document without any
                     extension
    :param make_pdf: Also create a PDF using the local graphviz installation
    :param print_tokens: Print the tokens as seen by the lexer to the console
    :param json: Print json to the console instead of text
    """
    if print_tokens:
        log.info('Tokens:')
        lexer.lexer.input(s)
        for tok in iter(lexer.lexer.token, None):
            log.info(repr(tok.type), repr(tok.value))
    root = parser.parse(s, (not reduced))

    if make_pdf:
        visualize.ast_dot(root, "%s.dot" % out_path)
        log.info("Graphviz written to %s.dot" % out_path)
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

    if print_json:
        program = [
            (opcode_to_cmd[inst[0]].upper(), inst[1], inst[2])
            for inst in program
        ]
        json.dump(program, sys.stdout)
    else:
        log.info("Instructions for VM:")
        instructions.prettyprint_program(program)

def parse(s):
    """
    Converts a regular expression into bytecode for the VM

    :param s: A regular expression
    :return: A list of opcode tuples in the form `[(opcode, arg1, arg2)]`
    """
    instr_list = parser.parse(s).generate_instructions()
    instr_list.append(instructions.Instruction('match'))
    return instructions.serialize(instr_list)

def main(args):

    short_opts =  'hvj'
    long_opts = [
        'help', 'version', 'json'
    ]

    try:
        opts, args = getopt(args, short_opts, long_opts)
    except GetoptError, err:
        logger.error(err)
        usage(error_codes['option'])

    json = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-v', '--version'):
            version()
        elif opt in ('-j', '--json'):
            json = True

    if len(args) != 1:
        logger.error("Expected exactly 1 regex got %d args" % len(args))
        usage(error_codes['option'])

    show(args[0], print_json=json, make_pdf=False, print_tokens=False)

if __name__ == "__main__":
    parser.debug = False
    main(sys.argv[1:])

