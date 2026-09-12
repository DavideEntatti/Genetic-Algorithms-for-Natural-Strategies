import random
from MyGA.strategy.agent import Agent
from MyGA.strategy.ASTNode import ASTNode

class Strategy:
    def __init__(self, n):
        self.agents = [Agent() for i in range(n)]

    def get_strategy(self, coalition = None):
        strat = ""
        for i, agent in enumerate(self.agents):
            if i != 0:
                strat += '\n'
            if not coalition:
                strat += "Agent"+str(i+1)+": "
            else:
                strat += "Agent"+str(coalition[i]+1)+": "
            for rule in agent.rules:
                strat += ASTNode.DSF_search(rule[0])
                strat += " -> "+rule[1]+", "
        return strat[:-2]
    
    # def randomize(self, agents_actions, cgs_aps, k):
    #     for i,agent in enumerate(self.agents):
    #         agent.actions = agents_actions[i]
    #     nodes_left = k #- len(agents_actions)
    #     conditions = list()
    #     while nodes_left >= 0:
    #         cond  = ASTNode()
    #         #nodes usato come coda BSF
    #         nodes = [cond]
    #         while nodes and nodes_left>=0:
    #             node = nodes.pop()
    #             #ottengo gli operatori validi per i figli e il loro numero
    #             ops, n_children = ASTNode.valid_operators(node.op)

    #             for i in range(n_children):
    #                 child = ASTNode()
    #                 if nodes_left < 3:
    #                     if 'DUAL' in ops:
    #                         ops.remove('DUAL')
    #                 if nodes_left < 2:
    #                     if 'NOT' in ops:
    #                         ops.remove('NOT')
    #                 op = random.choice(ops)
    #                 child.op = op
    #                 if op == 'VAR':
    #                     child.value = random.choice(cgs_aps)
    #                 elif op == 'DUAL':
    #                     child.value = random.choice(['AND','OR'])
    #                 if node.op:
    #                     node.children.append(child)
    #                 else:
    #                     cond = child
    #                 nodes.append(child)
    #                 nodes_left -=1

    #         #Se ho superto k, non aggiungo l'ultima funzione
    #         if nodes_left < 0:
    #             break
    #         conditions.append(cond)

    #     for cond in conditions:
    #         agent_idx = random.randrange(len(self.agents))
    #         agent = self.agents[agent_idx]
    #         agent.add_rule((cond, random.choice(agents_actions[agent_idx])))

    #     return self

    def randomize(self, agents_actions, cgs_aps, k):
        for i,agent in enumerate(self.agents):
            agent.actions = agents_actions[i]
            nodes_left = k #- len(agents_actions)
            conditions = list()
            while nodes_left >= 0:
                cond = ASTNode()
                #nodes usato come coda BSF
                nodes = [cond]
                while nodes and nodes_left>=0:
                    node = nodes.pop()
                    #ottengo gli operatori validi per i figli e il loro numero
                    ops, n_children = ASTNode.valid_operators(node.op)
    
                    for i in range(n_children):
                        child = ASTNode()
                        if nodes_left < 3:
                            if 'DUAL' in ops:
                                ops.remove('DUAL')
                        if nodes_left < 2:
                            if 'NOT' in ops:
                                ops.remove('NOT')
                        op = random.choice(ops)
                        child.op = op
                        if op == 'VAR':
                            child.value = random.choice(cgs_aps)
                        elif op == 'DUAL':
                            child.value = random.choice(['AND','OR'])
                        if node.op:
                            node.children.append(child)
                        else:
                            cond = child
                        nodes.append(child)
                        nodes_left -=1
    
                #Se ho superto k, non aggiungo l'ultima funzione
                if nodes_left < 0:
                    break
                conditions.append(cond)

            for cond in conditions:
                agent.add_rule((cond, random.choice(agent.actions)))
        return self



    def get_k(self):
        #k=0
        return max(agent.get_k() for agent in self.agents)
        # for agent in self.agents:
        #     k+=agent.get_k()
        # return k

    def copy(self):
        new_strat = Strategy(len(self.agents))
        for i in range(len(self.agents)):
            new_strat.agents[i].actions = self.agents[i].actions
            for rule in self.agents[i].rules:
                new_strat.agents[i].add_rule(Strategy.copy_rule(rule))
        return new_strat
    
    @staticmethod
    def copy_rule(rule):
        cond = rule[0].copy()
        return(cond, rule[1])


# class Agent:
#     #la rule è una tupla (condition, action)
#     def __init__(self):
#         self.rules = [Agent.default()]
#         self.actions = ["IDLE"]
#     def add_rule(self, rule):
#         for r in self.rules:
#             if Strategy.equal_rules(r, rule):
#                 return False
#         self.rules.insert(-1, rule)
#         return True
#     def get_action(self, state_props):
#         for rule in self.rules:
#             if rule[0].evaluate(state_props): return rule[1]
#     def get_k(self):
#         k=0
#         for rule in self.rules:
#             k+=rule[0].get_k()
#         return k

#     @staticmethod
#     def default():
#         return (ASTNode.default(), "IDLE")