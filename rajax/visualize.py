"""
Convert a tree of nodes following the :py:class:`rajax.ast.Node` interface into
a graphviz document
"""

# Steve Johnson, January 2009
# steve.johnson.public@gmail.com

header_string =         "digraph %s {\n    node [shape=box];\n"
subgraph_prefix =       "    {\n        rank=same; \n"
node_string_nocolor =   "        %s [label=\"%s\"];\n"
node_string_color =     "        %s [label=\"%s\", style=filled, fillcolor=\"%s\"];\n"
subgraph_postfix =      "    }\n"
edge_string =           "    %s -> %s;\n"
footer_string =         "}\n"
 
class Node(object):
    """
    Example node class with the proper attributes
    
    .. py:attribute: graph_id

        Leave blank

    .. py:attribute: string
    
        Text to put on node label

    .. py:attribute: children
    
        ``[Node, ...]``

    .. py:attribute: graph_color
    
        If present, should be a color such as ``#ffffff`` to be used as the
        node background color

    """
    def __init__(self, string, children=[]):
        super(Node, self).__init__()
        self.graph_id = ""
        self.string = string
        self.children = children

    def __str__(self):
        return self.string
 

node_count = 0
 

def ast_walk_tree(node, rank, subgraph_list=[]):
    global node_count
    node_count += 1
    node.graph_id = str(node_count)

    if len(subgraph_list)-1 < rank:
        subgraph_list.append([])

    subgraph_list[rank].append(node)

    for child in node.children:
        ast_walk_tree(child, rank+1, subgraph_list)

    return subgraph_list


def ast_dot(root, path, name="AST"):
    """
    Convert a tree of nodes following the L{Node} interface into a graphviz document

    @param root: Root node
    @param path: Path to the output file
    @param name: Name of the graph (optional)
    """
    f = open(path, 'w')
    f.write(header_string % name)

    global node_count
    node_count = 0

    subgraph_list = ast_walk_tree(root, 0, [])
    for subgraph in subgraph_list:
        f.write(subgraph_prefix)
        for node in subgraph:
            if hasattr(node,"graph_color"):
                f.write(node_string_color % (node.graph_id, str(node), node.graph_color))
            else:
                f.write(node_string_nocolor % (node.graph_id, str(node)))
        f.write(subgraph_postfix)

    for subgraph in subgraph_list:
        for node in subgraph:
            for child in node.children:
                f.write(edge_string % (node.graph_id, child.graph_id))
    f.write(footer_string)
