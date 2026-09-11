from MyGA.models.cgs.cgs_functions import read_CGS, prune, cgs_to_kripke
import networkx as nx
import spot

def display_CGS(model_path, strategy=None, formula_info=None):

    style_standard = {
        "background": "rgba(151, 194, 252, 0.4)", # Sfondo azzurro semi-trasparente
        "border": "rgba(43, 124, 233, 1)",        # Bordo blu opaco
        "highlight": {                            
            "background": "rgba(151, 194, 252, 1)",
            "border": "rgba(43, 124, 233, 1)"
        },
        "hover": {
            "background": "rgba(151, 194, 252, 1)",
            "border": "rgba(43, 124, 233, 1)"
        }
    }

    style_initial = {
        "background": "rgba(255, 204, 0, 0.4)",   # Sfondo giallo semi-trasparente
        "border": "rgba(255, 153, 0, 1)",         # Bordo arancione opaco
        "highlight": {
            "background": "rgba(255, 204, 0, 1)",
            "border": "rgba(255, 153, 0, 1)"
        },
        "hover": {
            "background": "rgba(255, 204, 0, 1)",
            "border": "rgba(255, 153, 0, 1)"
        }
    }

    style_accepting = {
        "background": "rgba(46, 204, 113, 0.4)",   # Sfondo verde semi-trasparente
        "border": "rgba(39, 174, 96, 1)",         # Bordo verde scuro
        "highlight": {
            "background": "rgba(46, 204, 113, 1)",
            "border": "rgba(39, 174, 96, 1)"
        },
        "hover": {
            "background": "rgba(46, 204, 113, 1)",
            "border": "rgba(39, 174, 96, 1)"
        }
    }

    cgs, agent_actions, aps = read_CGS(model_path)
    pruned_cgs = None
    if strategy:
        pruned_cgs = prune(cgs, strategy, formula_info[1])
        b_dict = spot.make_bdd_dict()
        pruned_kripke_graph = cgs_to_kripke(pruned_cgs, b_dict)
        is_accepting_state = get_accepting_states(pruned_kripke_graph, formula_info[0], b_dict)
        is_in_path = get_path_states(pruned_kripke_graph, is_accepting_state)


    G = nx.DiGraph()

    for src_idx, state in enumerate(cgs.states):
        matrix_prop = [row.copy() if isinstance(row, list) else row for row in cgs.matrix_prop]
        atomic_props = [str(p) for p in cgs.atomic_propositions.copy()]
        active_props = [atomic_props[p_idx] for p_idx, val in enumerate(matrix_prop[src_idx]) if val == 1]
        prop_str = ''
        for prop in active_props:
            prop_str += prop+', '
        if len(prop_str) > 0:
            prop_str = prop_str[:-2]
        full_label = str(state)+'\n'+prop_str
        if strategy and is_accepting_state[src_idx]:
            G.add_node(state, label=full_label, color=style_accepting)
        elif state == cgs.initial_state:
            G.add_node(state, label=full_label, color=style_initial)
        else:
            G.add_node(state, label=full_label, color=style_standard)

    for src_idx, row in enumerate(cgs.graph):

        for dst_idx, cell in enumerate(row):
            if not isinstance(cell, str) or not cell:
                continue

            if strategy and pruned_cgs.graph[src_idx][dst_idx] != 0 and is_in_path[dst_idx]:
                G.add_edge(cgs.states[src_idx], cgs.states[dst_idx], color='green', label=cell, weight=3)
            else:
                G.add_edge(cgs.states[src_idx], cgs.states[dst_idx], color='black', label=cell)

    return G

def get_accepting_states(model, formula, b_dict):
    buchi_automa = spot.translate(formula, "small", "buchi", dict=b_dict)
    product = spot.product(model, buchi_automa)
    mapping = product.get_product_states()
    sccs = spot.scc_info(product)
    is_accepting = [sccs.is_accepting_scc(sccs.scc_of(i)) for i in range(product.num_states())]
    is_accepting_state = [False]*model.num_states()
    for s in range(product.num_states()):
        if is_accepting[s]:
            is_accepting_state[mapping[s][0]] = True

    return is_accepting_state

def get_path_states(model, is_accepting_state):
    is_in_path = [is_accepting_state[i] for i in range(model.num_states())]
    changed = True
    while changed:
        changed = False
        for s in range(model.num_states()):
            if not is_in_path [s]:
                for edge in model.out(s):
                    if is_in_path [edge.dst]:
                        changed = True
                        is_in_path [s] = True
                        break
    return is_in_path