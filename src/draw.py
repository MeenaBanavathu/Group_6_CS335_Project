import pydot

class Node:
    def __init__(self,name,_type,is_array=0,ptr_level=0,children=None,_value=None,code=[]):
        self.name = name
        self._type = _type
        self.is_array = is_array
        self._value = _value
        self.ptr_level = ptr_level
        self.children = children
        self.code = code

def make_node(graph,nd,k='_'):
    if isinstance(nd,Node):
        make_ast(graph,nd,k)
        name = k+':'+str(nd.name)
    else:
        name = k+':'+str(nd)
        graph.add_node(pydot.Node(name))
    return name

def make_ast(graph,node,_k='_'):
    if node is None:
        graph.add_node(pydot.Node("None"))
        return "None"
    name = _k+':'+str(node.name)
    graph.add_node(pydot.Node(name))
    if not node._value is None:
        if isinstance(node._value,list):
            for i in node._value:
                if i is not None:
                    name2 = make_node(graph,i)
                    graph.add_edge(pydot.Edge(name,name2))
        else:
            name2 = make_node(graph,node._value)
            graph.add_edge(pydot.Edge(name,name2))
    if not node.children is None:
        for k,v in node.children.items():
            if isinstance(v,list):
                for i in v:
                    name2 = make_node(graph,i,k)
                    graph.add_edge(pydot.Edge(name,name2))
            else:
                name2 = make_node(graph,v,k)
                graph.add_edge(pydot.Edge(name,name2))



