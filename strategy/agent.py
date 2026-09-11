from MyGA.strategy.ASTNode import ASTNode

class Agent:
    #la rule è una tupla (condition, action)
    def __init__(self):
        self.rules = [Agent.default()]
        self.actions = ["IDLE"]
    def add_rule(self, rule):
        for r in self.rules:
            if Agent.equal_rules(r, rule):
                return False
        self.rules.insert(-1, rule)
        return True
    def get_action(self, state_props):
        for rule in self.rules:
            if rule[0].evaluate(state_props): return rule[1]
    def get_k(self):
        k=0
        for rule in self.rules:
            k+=rule[0].get_k()
        return k

    @staticmethod
    def default():
        return (ASTNode.default(), "IDLE")

    @staticmethod
    def equal_rules(rule1, rule2):
        if rule1[1] != rule2[1]:
            return False
        nodes1 = [rule1[0]]
        nodes2 = [rule2[0]]
        while nodes1 or nodes2:
            if not (nodes1 and nodes2):
                return False
            node1 = nodes1.pop()
            node2 = nodes2.pop()
            if node1.op != node2.op or node1.value != node2.value:
                return False
            if len(node1.children) != len(node2.children):
                return False
            if node1.children:
                nodes1 += node1.children
                nodes2 += node2.children
        return True