"""
Node classes in the AST, most of which generate code.

This module is a disaster area and should not be used as a model for writing
your own parser of any kind. Caveat lector.
"""

from instructions import Instruction, transform_classes
import const

all_chars = Instruction('char', 0, const.INF)

class ASTNode(object):
    """
    A basic node which maintains all basic attributes and passes control down
    the AST generically in :py:meth:`~rajax.ast.ASTNode.generate_instructions`

    .. py:attribute: node_type

        Label to put on a node in the graph, and to check type if necessary

    .. py_attribute: subtype

        The particular production which was matched

    .. py_attribute: children

        Ordered list of child nodes

    .. py_attribute: parent

        Parent node, not really used but might be useful later for optimizing
        AST transformations.

    .. py_attribute: data

        Any extra data, usually a character to be concatenated, or a duplicating operator

    .. py_attribute: string

        Property shortcut to ``__repr__`` because :py:mod:`rajax.visualize`
        needs it

    .. py_attribute: graph_id

        Used in :py:mod:`rajax.visualize`

    .. py_attribute: graph_color

        6-character sharped hex color which will be the node's background color
        in the graph (e.g. ``#ffffff``)
    """

    def __init__(self, node_type, subtype='', children=None, data=None):
        super(ASTNode, self).__init__()
        self.node_type = node_type
        self.subtype = subtype
        self.children = children or []
        self.parent = None
        self.data = data

        for child in self.children:
            child.parent = self

        # for visualization
        self.graph_id = ""
        self.graph_color = "#cccccc"
        if self.node_type == 're_expr' and self.subtype == 'concat':
            self.graph_color = "#eeeeee"

    def add_child(self, node):
        self.children.append(node)
        node.parent = self

    def generate_instructions(self, instr_list=None, flags=None):
        """
        Generate a list of Instruction objects starting at this node.

        These two lines of code must be at the start of every
        :py:meth:`~rajax.ast.ASTNode.generate_instructions()` implementation::

            instr_list = instr_list or []
            flags = flags or {}

        :param instr_list: An existing list of instructions. If left blank, a
                           new empty list will be created.
        :param flags: A dict of flags which is passed through all calls to
                      :py:meth:`~rajax.ast.ASTNode.generate_instructions`. Used
                      for generating code for matching/nonmatching bracket
                      expressions.
        :return: A list of Instruction objects
        """
        instr_list = instr_list or []
        flags = flags or {}
        for c in self.children:
            instr_list = c.generate_instructions(instr_list, flags)
        return instr_list

    def __repr__(self):
        if self.subtype:
            s1 = "%s_%s: " % (self.node_type, self.subtype)
        else:
            s1 = "%s: " % self.node_type
        if self.data:
            if isinstance(self.data, str) or (self.data > 0 and self.data != 2 << 15):
                if not isinstance(self.data, str):
                    try:
                        s2 = chr(self.data)
                    except ValueError:
                        s2 = str(self.data)
                else:
                    s2 = self.data
                if s2 in ['\n', '\r', '\t', '\f', '\v']:
                    s2 = const.esc_seq_for_str[s2]
                if s2.endswith('\\'):
                    s2 += "\\"
                elif s2.startswith('\\'):
                    s2 = "\\" + s2
                s1 += s2
            else:
                s1 += str(self.data)
        return s1

    string = property(__repr__)


class RegexNode(ASTNode):
    """Generates code for | operator"""

    def __init__(self, subtype, children):
        super(RegexNode, self).__init__("regex", subtype, children)
        if subtype == 'alt':
            self.graph_color = "#ccffff"

    def generate_instructions(self, instr_list=None, flags=None):
        """
        Generate code for a ``|`` operator if ``subtype == 'alt'``::

                split L1, L2
            L1: codes for e1
                jmp L3
            L2: codes for e2
            L3:

        If ``subtype != 'alt'``, then this node is reduced away during parsing.
        """
        instr_list = instr_list or []
        flags = flags or {}
        if self.subtype == 'alt':
            back_jump = len(instr_list)+1

            first_split = Instruction('split', back_jump, 'TEMP')
            instr_list.append(first_split)
            instr_list = self.children[0].generate_instructions(instr_list, flags)

            first_jump = Instruction('jmp', 'TEMP')
            instr_list.append(first_jump)
            first_split.arg2 = len(instr_list)

            instr_list = self.children[1].generate_instructions(instr_list, flags)
            first_jump.arg1 = len(instr_list)
            return instr_list
        return super(RegexNode, self).generate_instructions(instr_list, flags)


class NonDupReNode(ASTNode):
    """
    Generates code for characters.
    """

    def __init__(self, subtype, children=None, data=None):
        super(NonDupReNode, self).__init__('nondup_re', subtype, children, data=data)
        self.graph_color = "#ffffcc"

    def generate_instructions(self, instr_list=None, flags=None):
        """
        Generate code for a character if ``subtype == 'char'``::

            a       char 'a'
        """
        instr_list = instr_list or []
        flags = flags or {}
        if self.subtype == "char":
            if isinstance(self.data, int):
                d = self.data
            else:
                d = ord(self.data)
            instr_list.append(Instruction('char', d))
            return instr_list
        if self.subtype == 'group':
            instr_list = self.children[0].generate_instructions(instr_list, flags)
            return instr_list
        return super(NonDupReNode, self).generate_instructions(instr_list, flags)


class SimpleReNode(ASTNode):
    """Generates code for +, *, and ? operators"""

    def __init__(self, subtype, children=None, data=None):
        super(SimpleReNode, self).__init__("simple_re", subtype, children, data=data)
        if self.subtype == 'dup':
            self.graph_color = "#ccffcc"


        """
        Generate code for a +, *, or ? operator if ``subtype == 'dup'``.

        e+::

            L1: codes for e
                split L1, L3
            L3:

        e*::

            L1: split L2, L3
            L2: codes for e
                jmp L1
            L3:

        e?::

            split L1, L2
            L1: codes for e
            L2:

        """
        instr_list = []
        flags = {}
        if self.subtype == 'dup':
            lchild = self.children[0]
            if self.data == '+':
                back_jump = len(instr_list)
                instr_list = lchild.generate_instructions(instr_list, flags)
                forward_jump = len(instr_list) + 1
                instr_list.append(Instruction('split', back_jump, forward_jump))
                return instr_list
            if self.data == '*' or self.data == '?':
                back_jump = len(instr_list)+1

                first_split = Instruction('split', back_jump, 'TEMP')
                instr_list.append(first_split)

                instr_list = lchild.generate_instructions(instr_list)
                if self.data == '*':
                    instr_list.append(Instruction('jmp', back_jump-1))
                first_split.arg2 = len(instr_list)
                return instr_list
        else:
            return super(SimpleReNode, self).generate_instructions(instr_list, flags)


class RangeExprNode(ASTNode):
    """Generates code for range expressions inside bracket expressions"""

    def __init__(self, children):
        super(RangeExprNode, self).__init__("range_expr", children=children)
        self.graph_color = "#ffccff"

    def generate_instructions(self, instr_list=None, flags=None):
        """Generates code for a character range"""
        instr_list = instr_list or []
        flags = flags or {}
        if flags['matching']:
            instr_list.append(Instruction('char', ord(self.children[0].data), 
                                                  ord(self.children[1].data)))
        else:
            instr_list.append(Instruction('nchar', ord(self.children[0].data), 
                                                   ord(self.children[1].data)))
        return instr_list


class EndRangeNode(ASTNode):
    """
    Generates code for characters in a matching or non-matching bracket
    expression.
    """

    def __init__(self, subtype, children=None, data=None):
        super(EndRangeNode, self).__init__('end_range', subtype, children, data=data)
        self.graph_color = "#ccccff"

    def generate_instructions(self, instr_list=None, flags=None):
        """
        Generate C{char} or C{nchar} opcode depending on whether the character
        is in a matching or non-matching bracket expression
        """
        instr_list = instr_list or []
        flags = flags or {}
        if flags['matching']:
            instr_list.append(Instruction('char', ord(self.data)))
        else:
            instr_list.append(Instruction('nchar', ord(self.data)))
        return instr_list


class CharClassNode(ASTNode):
    """
    Pretends to be a chain of ``follow_list``s, obeys ``matching`` flag,
    complains if the user is doing something weird (see below). This class is a
    little bit odd with the intention of avoiding duplication of the code in
    :py:class:`~rajax.ast.BrackExprListNode`.
    """

    def __init__(self, char_class):
        super(CharClassNode, self).__init__("char_class", data=char_class)
        self.graph_color = "#ffcccc"

    def generate_instructions(self, instr_list=None, flags=None):
        """
        Use ``matching`` flag and presence of ``self.data`` in char class
        mapping dicts to determine what kind of instruction to return, and what
        its character arguments are
        """

        instr_list = instr_list or []
        flags = flags or {}

        if flags['matching']:
            # neg: [\W] = [^\w] so use nchar
            # And insert a BREAK because these should be separated
            if const.char_classes_nm.has_key(self.data):
                char_list = const.char_classes_nm[self.data]
                instr = 'nchar'
                if instr_list and instr_list[-1].cmd == 'nchar':
                    instr_list.append(Instruction('BREAK'))
            # pos: [\w] so use char
            if const.char_classes_m.has_key(self.data):
                char_list = const.char_classes_m[self.data]
                instr = 'char'
        else:
            # [^\Wab\D]
            # neg: [^\W] = [\w] so use char. Let BrackExprListNode sort out the details.
            if const.char_classes_nm.has_key(self.data):
                char_list = const.char_classes_nm[self.data]
                instr = 'char'
                if instr_list and instr_list[-1].cmd == 'char':
                    instr_list.append(Instruction('BREAK'))
            # pos: [^\w] so use nchar
            # But do not insert a BREAK because these should all be a global requirement
            if const.char_classes_m.has_key(self.data):
                char_list = const.char_classes_m[self.data]
                instr = 'nchar'
        # Most of char_classes_nm is just aliases to char_classes_m to save typing
        # An alias is indicated by a string which is a key to char_classes_m
        if isinstance(char_list, str):
            char_list = const.char_classes_m[const.char_classes_nm[self.data]]
        for char in char_list:
            if len(char) == 1:
                instr_list.append(Instruction(instr, ord(char[0])))
            else:
                instr_list.append(Instruction(instr, ord(char[0]), ord(char[1])))
        return instr_list


class BrackExprListNode(ASTNode):
    """Performs transformations and passes down flags in order to implement
    matching and nonmatching lists.
    """

    def __init__(self, subtype, children=None):
        super(BrackExprListNode, self).__init__("brack_expr", subtype, children)
        self.graph_color = "#ffffff"

    def generate_instructions(self, instr_list=None, flags=None):
        """
        Perform transformations and pass down flags in order to implement
        matching and nonmatching lists.

        For matching lists, generate a block of ``SPLIT``s, generate children's
        ``CHAR`` instructions, and interleave them between a series of
        ``JMP``s. Example::

            [abc]
            0:  split   1   3
            1:  split   2   5
            2:  jmp     7
            3:  char    a
            4:  jmp     9
            5:  char    b
            6:  jmp     9
            7:  char    c
            8:  match

        For nonmatching lists, just complement the set.
        Same for negative classes in matching lists.
        """

        instr_list = instr_list or []
        flags = flags or {}

        matching = (self.subtype == 'matching_list')
        newflags = {'matching': matching}

        # ================================================================
        # = Sort instrs generated by children into more manageable lists =
        # ================================================================

        new_instrs_temp = []
        for c in self.children:
            new_instrs_temp = c.generate_instructions(new_instrs_temp, newflags)
        # Character could be any of these:
        switch_instrs = []  # [[char], [nchar, nchar], ...]
        # But cannot be any of these:
        tailing_nchars = [] # [nchar, nchar, ...]
        if matching:
            for instr in new_instrs_temp:
                if instr.cmd == 'char':
                    switch_instrs.append([instr])
                elif instr.cmd == 'nchar':
                    switch_instrs.extend(transform_classes([[all_chars]], [instr]))
                elif instr.cmd == 'BREAK':
                    switch_instrs.append([])
        else:
            new_list_on_char = True
            for instr in new_instrs_temp:
                if instr.cmd == 'char':
                    if (new_list_on_char) or not switch_instrs:
                        switch_instrs.append([instr])
                    else:
                        switch_instrs[-1].append(instr)
                    new_list_on_char = False
                elif instr.cmd == 'nchar':
                    # These will have been generated by positive classes. We need to
                    # have the VM require *all* of them to hold.
                    new_list_on_char = True
                    tailing_nchars.append(instr)
                elif instr.cmd == 'BREAK':
                    # Only if the break was necessary
                    new_list_on_char = True
            if not switch_instrs:
                switch_instrs = [[Instruction('char', 0, 2 << 15)]]
            switch_instrs = transform_classes(switch_instrs, tailing_nchars)

        # ====================================
        # = Re-sort instrs and generate code =
        # ====================================
        if len(switch_instrs) == 1 and len(switch_instrs[0]) == 1:
            instr_list.append(switch_instrs[0][0])
        else:
            end_of_splits = len(instr_list) + len(switch_instrs)
            # Continue after one split per block, and one jmp per block except the last one
            end_of_jumps  = len(instr_list) + len(switch_instrs)*2 - 1 \
                          + sum([len(instrs) for instrs in switch_instrs])
            i = 0
            for instr in switch_instrs[:-1]:
                instr_list.append(Instruction('split', len(instr_list)+1, end_of_splits + i))
                i += 1 + len(instr)
            instr_list.append(Instruction('jmp', end_of_splits + i))
            for instrs in switch_instrs[:-1]:
                instr_list.extend(instrs)
                instr_list.append(Instruction('jmp', end_of_jumps))
            instr_list.extend(switch_instrs[-1])
        return instr_list
