"""
Mappings between opcodes and command strings, numerical constants

@var opcode_to_cmd: Dictionary mapping opcodes to commands
@var cmd_to_opcode: Dictionary mapping commands to opcodes
@var char_classes_m: Dictionary mapping escaped characters to lists of character ranges representing B{matching} character classes.
@var char_classes_nm: See C{char_classes_m} but for complemented character classes.
@var str_esc_seq: Dictionary mapping string escape sequence letters to characters
"""

# Steve Johnson, January 2009
# steve.johnson.public@gmail.com

# Mapping numerical opcodes to command strings
opcode_to_cmd = {
    0: 'match',
    1: 'char',
    2: 'split',
    3: 'jmp',
    4: 'nchar',
}

# Also define them as integer constants, mostly for readability in the VM
MATCH = 0
CHAR = 1
SPLIT = 2
JMP = 3
NCHAR = 4

# Other constants
WILDCARD = 0x11FFFF
# Highest possible unicode value, from http://unifoundry.com/unicode-tutorial.html
INF = 0x10FFFF

# Reversing the mapping. Let's hope no two opcodes point to the same 
# command string.
cmd_to_opcode = {}
for k, v in opcode_to_cmd.iteritems():
    cmd_to_opcode[v] = k

char_classes_m = {
    's': ['\n', '\r', '\t', '\f', '\v'],
    'd': [('0','9')],
    'w': [('0','9'), ('a','z'), ('A','Z'), '_']
}

# If one of these is *not* the opposite of a matching char, give it a list
# in the style of char_classes_m.
char_classes_nm = {
    'S': 's',
    'D': 'd',
    'W': 'w',
}

str_esc_seq = {
    't': '\t',
    'n': '\n',
    'r': '\r',
    'f': '\f',
    'v': '\v',
}

# Reverse this one too for use in ASTNode.__repr__
esc_seq_for_str = {}
for k, v in str_esc_seq.iteritems():
    esc_seq_for_str[v] = k
