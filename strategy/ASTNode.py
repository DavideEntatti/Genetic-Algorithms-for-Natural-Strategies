import random

class ASTNode:
    def __init__(self, op = None, children=None, value=None):
        self.op = op # 'AND', 'OR', 'NOT', 'VAR', 'CONST'4e
        self.children = children or []
        self.value = value # Nome della variabile se op == 'VAR'

    def evaluate(self, state_props):
        if self.op == 'CONST': return True #Una costane ha senso sole se è True ed è un nodo radice
        if self.op == 'VAR': return self.value in state_props
        if self.op == 'NOT': return not self.children[0].evaluate(state_props)
        if self.op == 'DUAL':
            if self.value == 'AND': return all(c.evaluate(state_props) for c in self.children)
            if self.value == 'OR':  return any(c.evaluate(state_props) for c in self.children)

    def get_k(self):
        if self.op == 'CONST':
            return 0
        k=1
        for child in self.children:
            k+=child.get_k()
        return k


    def get_nodes_with_depth(self, parent, index, d):
        nodes = [(self, parent, index, d)]
        for i, child in enumerate(self.children):
            nodes += child.get_nodes_with_depth(self, i, d+1)
        return nodes
               
    def copy(self):
        new_node = ASTNode(self.op, value=self.value)
        new_node.children = [c.copy() for c in self.children]
        return new_node
        

    @staticmethod
    def default():
        return ASTNode("CONST")
    
    @staticmethod
    def DSF_search(node):
        if node.op == 'CONST':
            return "True"
        if node.op == 'VAR':
            return str(node.value)
        if node.op == 'NOT':
            return node.op+" "+ASTNode.DSF_search(node.children[0])
        else:
            return "("+ASTNode.DSF_search(node.children[0])+" "+node.value+" "+ASTNode.DSF_search(node.children[1])+")"
        
    @staticmethod
    def valid_operators(op): #Ritorna gli operatori validi per i figli e il numero di figli
        if op == 'CONST' or op == 'VAR':
            return (None, 0)
        if op == 'NOT':
            return (['VAR', 'DUAL'], 1)
        if op == 'DUAL':
            return (['VAR', 'NOT', 'DUAL',], 2)
        return (['VAR', 'NOT', 'DUAL'], 1)