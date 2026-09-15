import spot

from model_checker.parsers.game_structures.cgs import CGS
from model_checker.parsers.game_structures.cgs.cgs_actions import extract_actions_for_agents
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    AGENT_ACTION_SEPARATOR,
    JOINT_CHOICE_SEPARATOR,
    normalize_action_token,
)


def prune(cgs: CGS, strategy, coalition):
    """Return a pruned Vitamin CGS that keeps only strategy-consistent transitions."""
    pruned_cgs = CGS()
    # For Vitamin CGS, directly copy the internal representation instead of using read_from_model_object
    pruned_cgs.graph = [row.copy() for row in cgs.graph]
    pruned_cgs.states = cgs.states.copy()
    pruned_cgs.atomic_propositions = cgs.atomic_propositions.copy()
    pruned_cgs.matrix_prop = [row.copy() if isinstance(row, list) else row for row in cgs.matrix_prop]
    pruned_cgs.initial_state = cgs.initial_state
    pruned_cgs.number_of_agents = cgs.number_of_agents
    pruned_cgs.actions = cgs.actions.copy() if cgs.actions else []
    pruned_cgs.unknown_transition_matrix = [row.copy() for row in cgs.unknown_transition_matrix]
    pruned_cgs.invalidate_caches()

    atomic_props = [str(p) for p in pruned_cgs.atomic_propositions.copy()]
    matrix_prop = pruned_cgs.matrix_prop
    graph = [row.copy() for row in pruned_cgs.graph]

    for src_idx, row in enumerate(graph):
        active_props = [atomic_props[p_idx] for p_idx, val in enumerate(matrix_prop[src_idx]) if val == 1]

        for dst_idx, cell in enumerate(row):
            if not isinstance(cell, str) or not cell:
                continue

            if cell == '*':
                graph[src_idx][dst_idx] = '*'
                continue

            joint_choices = [part.strip() for part in cell.split(JOINT_CHOICE_SEPARATOR) if part.strip()]
            filtered_choices = []

            for joint in joint_choices:
                if AGENT_ACTION_SEPARATOR in joint:
                    tokens = [normalize_action_token(t) for t in joint.split(AGENT_ACTION_SEPARATOR)]
                else:
                    tokens = [normalize_action_token(ch) for ch in joint]

                is_consistent = True
                for strat_agent_index, cgs_agent_idx in enumerate(coalition):
                    if cgs_agent_idx >= len(tokens):
                        is_consistent = False
                        break

                    required_action = strategy.agents[strat_agent_index].get_action(active_props)
                    if tokens[cgs_agent_idx] != required_action and tokens[cgs_agent_idx] != '*':
                        is_consistent = False
                        break

                if is_consistent:
                    filtered_choices.append(joint)

            if filtered_choices:
                graph[src_idx][dst_idx] = JOINT_CHOICE_SEPARATOR.join(filtered_choices)
            else:
                graph[src_idx][dst_idx] = 0

        if(all(cell == 0 for cell in row)):
            row[src_idx] = '*'

    pruned_cgs.graph = graph
    
    return pruned_cgs


def cgs_to_kripke(cgs: CGS, b_dict):
    """Translate a Vitamin CGS into a Spot automaton using state labelling."""
    model = spot.make_twa_graph(b_dict)

    atomic_props = [str(p).strip() for p in cgs.atomic_propositions.copy()]
    for prop in atomic_props:
        model.register_ap(prop)

    state_map = {}
    for state in cgs.states.copy():
        state_map[str(state)] = model.new_state()

    init_key = cgs.initial_state

    model.set_init_state(state_map[init_key])

    matrix_prop = cgs.matrix_prop

    for src_idx, row in enumerate(cgs.graph):
        src_state = str(cgs.get_state_name_by_index(src_idx))
        props_string = ""
        if atomic_props:
            atoms = []
            for prop, val in zip(atomic_props, matrix_prop[src_idx]):
                atoms.append(prop if val == 1 else f"!{prop}")
            props_string = " & ".join(atoms)
        else:
            props_string = "True"

        cond = spot.formula_to_bdd(spot.formula(props_string), b_dict, model)

        for dst_idx, cell in enumerate(row):
            if cell == 0:
                continue
            dst_state = str(cgs.get_state_name_by_index(dst_idx))
            model.new_edge(state_map[src_state], state_map[dst_state], cond)

    return model

def complete(model):
    b_dict = model.get_dict()
    cond = spot.formula_to_bdd("true", b_dict, b_dict)
    deadlocks = []
    for s in range(model.num_states()):
        has_out = any(True for _ in model.out(s))
        if not has_out:
            deadlocks.append(s)
            model.new_edge(s,s,cond)
    return deadlocks

def read_CGS(model_path):
    cgs = CGS()
    cgs.read_file(str(model_path))

    transition_matrix=[]

    for row in cgs.graph:
        transition_matrix.append(row)

    raw_actions = extract_actions_for_agents(transition_matrix, list(range(1, cgs.get_number_of_agents()+1)))
    #print(raw_actions)
    num_agents = cgs.get_number_of_agents()
    agents_actions = {i: raw_actions.get(f'agent{i+1}', []) for i in range(num_agents)}
    #print(agents_actions)
    aps = [str(p) for p in cgs.atomic_propositions.copy()]

    return cgs, agents_actions, aps