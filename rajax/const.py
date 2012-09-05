"""
Mappings between opcodes and command strings, numerical constants
"""

#: Mapping numerical opcodes to command strings
opcode_to_cmd = {
    0: 'match',
    1: 'char',
    2: 'split',
    3: 'jmp',
    4: 'nchar',
}

#: Also define them as integer constants, mostly for readability in the VM
MATCH = 0
CHAR = 1
SPLIT = 2
JMP = 3
NCHAR = 4

# Other constants
WILDCARD = 0x11FFFF
# Highest possible unicode value, from http://unifoundry.com/unicode-tutorial.html
INF = 0x10FFFF

#: Map command strings back to opcodes
cmd_to_opcode = {}
for k, v in opcode_to_cmd.iteritems():
    cmd_to_opcode[v] = k

#: Map character escape sequences to ranges of characters
char_classes_m = {
    's': ['\n', '\r', '\t', '\f', '\v'],
    'd': [('0','9')],
    'w': [('0','9'), ('a','z'), ('A','Z'), '_']
}

#: Complement character classes.
#: If one of these is *not* the opposite of a matching char, give it a list
#: in the style of char_classes_m.
char_classes_nm = {
    'S': 's',
    'D': 'd',
    'W': 'w',
}

#: String escape sequences. Wish I knew an easy way to just inherit all the
#: Python ones.
str_esc_seq = {
    't': '\t',
    'n': '\n',
    'r': '\r',
    'f': '\f',
    'v': '\v',
}

#: Map character back to its escape sequence
esc_seq_for_str = {}
for k, v in str_esc_seq.iteritems():
    esc_seq_for_str[v] = k
