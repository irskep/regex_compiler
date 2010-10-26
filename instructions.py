"""
Classes and functions for working with VM instructions
"""

# Steve Johnson, January 2009
# steve.johnson.public@gmail.com

from const import *

class Instruction(object):
    """Represents a single VM instruction with a command and two optional arguments"""
    
    def __init__(self, cmd, arg1=None, arg2=None):
        self.cmd = cmd
        self.arg1 = arg1
        self.arg2 = arg2
    
    def to_opcode(self):
        """
        Alias for L{make_opcode}
        """
        return make_opcode(self.cmd, self.arg1, self.arg2)
    
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        return str((self.cmd, self.arg1, self.arg2))
    

def _range_intersect(a1, a2, b1, b2):
    # (0, 10), (10, 20): (10, 10)
    if a2 == b1:
        return a2, a2
    # (10, 20), (0, 10): (10, 10)
    if b2 == a1:
        return b2, b2
    # (5, 10), (0, 10): (5, 10)
    if b1 <= a1 < b2:
        return a1, b2
    # (0, 10), (5, 10): (5, 10)
    if a1 <= b1 < a2:
        return a1, b1
    return None

def _range_matches_class(a1, a2, char_class):
    current_range = None
    for range_to_match in char_class:
        b1, b2 = range_to_match.arg1, range_to_match.arg2 or range_to_match.arg1
        current_range = current_range or _range_intersect(a1, a2, b1, b2)
    return current_range

def _remove_from_range(r, b1, b2):
    if b2 < r[0] or b1 > r[1]:
        return [r]
    if b2 == r[0] and r[1] - r[0] > 0:
        return [(r[0] + 1, r[1])]
    if b1 == r[1] and r[1] - r[0] > 0:
        return [(r[0], r[1] - 1)]
    if b1 > r[0] and b2 < r[1]:
        return [(r[0], b1 - 1), (b2 + 1, r[1])]
    return []

def transform_classes(classes, excludes):
    """
    This is a really cool function which I will explain later.
    """
    working_set = set()
    for char_class in classes:
        for char_range in char_class:
            modified_range = True
            for char_class_check in classes:
                modified_range = modified_range and _range_matches_class(
                                                        char_range.arg1, 
                                                        char_range.arg2 or char_range.arg1,
                                                        char_class_check)
            if modified_range:
                working_set.add(modified_range)
    next_set = set()
    for exclude in excludes:
        b1, b2 = exclude.arg1, exclude.arg2 or exclude.arg1
        for char_range in working_set:
            for modified_range in _remove_from_range(char_range, b1, b2):
                next_set.add(modified_range)
        working_set = next_set
        next_set = set()
    return [[Instruction('char', r[0], r[1])] for r in working_set]

def make_opcode(cmd, arg1, arg2=None):
    """
    Convert an Instruction to an opcode tuple.
    
    Converts cmd to an opcode, converts arg1 and arg2 to ints (zero if None, 
    ord(c) if character), and return as a tuple
    
    @rtype: C{(opcode, arg1, arg2)}
    """
    arg1 = ord(arg1) if isinstance(arg1, str) else arg1 or 0
    arg2 = ord(arg2) if isinstance(arg2, str) else arg2 or 0
    return (cmd_to_opcode[cmd], arg1, arg2)

def serialize(instr_list):
    """
    Convert a list of instructions into a list of opcode tuples
    
    @rtype: C{[(opcode, arg1, arg2),]}
    """
    return [make_opcode(i.cmd, i.arg1, i.arg2) for i in instr_list]

def prettyprint_program(opcode_list):
    """
    Print a formatted list of the entire program in human-readable form
    
    @param opcode_list: A list of opcode tuples, probably returned by compiler.parse()
    """
    instr_list = []
    specials = {INF: 'INF', WILDCARD: 'WILD', 0: 'ZERO'}
    for o in opcode_list:
        i = Instruction(opcode_to_cmd[o[0]], o[1], o[2])
        if i.cmd == 'char':
            if isinstance(i.arg1, int):
                try:
                    i.arg1 = specials[i.arg1]
                except KeyError:
                    i.arg1 = chr(i.arg1)
            if isinstance(i.arg2, int):
                try:
                    i.arg2 = specials[i.arg2]
                except KeyError:
                    i.arg2 = chr(i.arg2)
        instr_list.append(i)
    j = 0
    s1 = len(str(len(instr_list))) #yeah, I know, cheap
    s2 = max([i.arg1 for i in instr_list])
    for i in instr_list:
        if i.arg2:
            print "%s: %s %3s %3s" % (str(j).rjust(s1), i.cmd.ljust(5), 
                                    str(i.arg1), str(i.arg2))
        elif i.arg1 or i.cmd == 'jmp':
            print "%s: %s %3s" % (str(j).rjust(s1), i.cmd.ljust(5), 
                                 str(i.arg1))
        else:
            print "%s: %s" % (str(j).rjust(s1), i.cmd.ljust(5))
        j += 1
