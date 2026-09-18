from MyGA.strategy.strategy import Strategy
from MyGA.strategy.agent import Agent
from MyGA.strategy.ASTNode import ASTNode
from MyGA.config import config
import random

def new_population(n, agents_actions, aps, k):
    n_agents = len(agents_actions)
    population = [(Strategy(n_agents).randomize(agents_actions, aps, k),None) for i in range(n)]
    return population

def new_generation(population, agents_actions, aps, k, elite=True):
    # Ensure we don't index past the current population when N_ELITE
    if elite:
        elite_count = min(config.N_ELITE, len(population))
    else:
        elite_count = 0
    elite = [population[n] for n in range(elite_count)]

    extra = new_population(config.EXTRA_STRATEGIES, agents_actions, aps, k)
    # Compute how many children to produce (non-negative)
    n_children = max(0, config.POPULATION_SIZE - elite_count - config.EXTRA_STRATEGIES)
    population = elite + recombination(population, agents_actions, aps, k, n_children) + extra

    return population

def recombination(population, agents_actions, aps, k, n_children=None):
    if n_children is None:
        n_children = max(0, config.POPULATION_SIZE - config.N_ELITE - config.EXTRA_STRATEGIES)
    new_population = []
    # If population too small, tournament selection will adapt
    while len(new_population) < n_children:
        parent1 = tournament_selection(population)
        parent2 = tournament_selection(population)
        new_population.append((make_child(parent1, parent2, agents_actions, aps, k), None))
    return new_population

def tournament_selection(population):
    #Scelgo il migiore tra le strategie selezionate
    # If the configured tournament size is larger than current population,
    # sample with the available size (sample without replacement).
    ts = max(min(config.TOURNAMENT_SIZE, len(population)),1)
    if ts <= 0:
        return population[0]
    tournament = random.sample(population, ts)
    tournament.sort(key=lambda x: x[1])
    return tournament[0][0] if isinstance(tournament[0], tuple) else tournament[0]

def make_child(parent1, parent2, agents_actions, aps, k):
    n_agents = len(parent1.agents)
    child_strat = Strategy(n_agents)

    for i in range(n_agents):
        #scelgo le prime n regole di parent1 e le ultime m di parent2
        #-1 per non selezionare la regola di default
        rules = []
        p1_rules = parent1.agents[i].rules[:-1]
        p2_rules = parent2.agents[i].rules[:-1]
        # if p1_rules:
        #     cut1 = random.randrange(0, len(p1_rules))
        #     rules1 = parent1.agents[i].rules[:cut1]
        #     rules += rules1
        # if p2_rules:
        #     cut2 = random.randrange(0, len(p2_rules))
        #     rules2 = parent2.agents[i].rules[cut2:]
        #     rules += rules2
        #Instead of random cuts, just take half from each parent
        half1 = len(p1_rules) // 2
        half2 = len(p2_rules) // 2
        rules += p1_rules[:half1] + p2_rules[half2:]
        rules = [Strategy.copy_rule(r) for r in rules]

        if(rules):
            if random.random() < config.ORDER_MUTATION and len(rules) > 1:
                rule = rules.pop(random.randrange(len(rules)))
                rules.insert(random.randrange(len(rules) + 1), rule)

            for r in range(len(rules)):
                if random.random() < config.ACTION_MUTATION:
                    actions = agents_actions[i]
                    rules[r] = (rules[r][0].copy(), random.choice(actions))
                if random.random() < config.CONDITION_MUTATION:
                    rules[r] = (mutate(rules[r][0], aps), rules[r][1])
            
            for rule in rules:
                child_strat.agents[i].add_rule(rule)
    
    #Controllo per k e aggiungo default alla fine della riproduzione
    while child_strat.get_k() > k:
        # collect removable (non-default) rules
        complex_agents = [ag for ag in child_strat.agents if ag.get_k() > k]
        removable = [(ag, r) for ag in complex_agents for r in ag.rules[:-1]]
        if not removable:
            # nothing to remove, break to avoid infinite loop
            break
        ag, rule = random.choice(removable)
        ag.rules.remove(rule)

    return child_strat

def mutate(cond, aps):
    #Lista di tutti i nodi con associato il genitore, l'indice del figlio e la profondità
    nodes_info = cond.get_nodes_with_depth(None, None, 1)
    w = [n[3] for n in nodes_info]
    selected = random.choices(nodes_info, weights=w, k=1)[0]

    #Salvo i dati del nodo selezionato in più variabili
    node = selected[0]
    parent = selected[1]
    index = selected[2]
    
    if node.op == 'NOT':#Se pesco un nodo 'NOT' lo rimuovo
        if parent:
            parent.children[index] = node.children[0]
            return cond
        else: 
            return node.children[0]
    else:
        #Scelgo tra aggiunta not, cambio operatore, cambio valore
        choice = random.randint(0,2)

        if choice == 0:#Aggiungo nodo 'NOT'
            new_node = ASTNode('NOT', children = [node])
            if parent and parent.op != 'NOT':
                parent.children[index] = new_node
            elif node.op != 'CONST':
                return new_node

        elif choice == 1:#Cambio il tipo di operatore
            if node.op == 'VAR' or node.op == 'CONST':
                node.op = 'DUAL' #Aggiungo due proposizioni atomiche come figli
                node.children = [ASTNode('VAR',value=random.choice(aps)), ASTNode('VAR',value=random.choice(aps))]
            elif node.op == 'DUAL':
                if not parent: #Il nodo radice può essere una costante
                    node.op = 'VAR'
                    node.children.clear()

        if choice == 1 or choice ==2:#Cambio il valore del nodo
            if node.op == 'VAR':
                node.value = random.choice(aps)
            elif node.op == 'DUAL':
                node.value = random.choice(['AND','OR'])

    return cond