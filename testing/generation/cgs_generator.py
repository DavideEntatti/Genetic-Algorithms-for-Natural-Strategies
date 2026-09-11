"""Generate random CGS models and test formulas for search_strategy evaluation."""
import random
import itertools
from pathlib import Path

from model_checker.parsers.game_structures.cgs.cgs_actions import (
    AGENT_ACTION_SEPARATOR,
    JOINT_CHOICE_SEPARATOR,
    IDLE_TOKENS
)

#AGENT_ACTION_SEPARATOR = ''

def generate_random_cgs(
    num_states: int = 4,
    num_agents: int = 2,
    num_propositions: int = 4,
    num_agent_actions: int = 3,
    sparsity: float = 0.5,
    seed: int | None = None,
) -> str:
    """Generate a random CGS model in Vitamin format.
    
    Args:
        num_states: Number of states (s0, s1, ..., s{num_states-1})
        num_agents: Number of agents
        num_propositions: Number of atomic propositions
        num_agent_actions: Number of actions available to each agent
        sparsity: Average number of transitions per state; lower = sparser graph
        seed: Random seed for reproducibility
        
    Returns:
        CGS model in Vitamin text format
    """
    if seed is not None:
        random.seed(seed)
    
    # Generate state names
    states = [f"s{i}" for i in range(num_states)]
    
    # Generate proposition names
    current_prop = 'p'
    props = []
    i = 0
    overflow = 0
    while(i<num_propositions):
        if ord(current_prop) > ord('z'):
            overflow+=1
            current_prop = 'p'
        if overflow == 0:
            props.append(current_prop)
        else:
            props.append(current_prop+f'{overflow}')
        current_prop = chr(ord(current_prop)+1)
        i+=1
    
    idle_token = 'I'
    if idle_token not in IDLE_TOKENS:
        raise ValueError(f"Idle token '{idle_token}' is not in IDLE_TOKENS: {IDLE_TOKENS}")

    # Build transition matrix: random joint actions between states
    # Format: each cell is either '0' (no transition) or a joint action like 'A|B'

    # Available actions per agent
    current_action = 'A'
    agent_actions = ['I']
    i = 0
    overflow = 0
    while(i<num_agent_actions):
        if ord(current_action) > ord('O'):
            overflow+=1
            current_action = 'A'
        if overflow == 0:
            agent_actions.append(current_action)
        else:
            agent_actions.append(current_action+f'{overflow}')
        current_action = chr(ord(current_action)+1)
        i+=1

    all_possible_joints = list(AGENT_ACTION_SEPARATOR.join(joint) for joint in itertools.product(agent_actions, repeat=num_agents))
    idle_joint = AGENT_ACTION_SEPARATOR.join(idle_token for _ in range(num_agents))
    all_possible_joints.remove(idle_joint)  # Remove idle joint from random selection
    
    transitions = []
    for src in range(num_states):
        row = []
        row_joints = random.sample(all_possible_joints, min(int(num_states*sparsity),len(all_possible_joints)))  # Randomly select joint actions for this row
        joints_destinations = list(list() for _ in range(num_states))
        joints_destinations[src].append(idle_joint)  # Ensure self-loop with idle joint
                    
        for joint in row_joints:
            dst = random.randint(0, num_states - 1)
            joints_destinations[dst].append(joint)
        for dst in range(num_states):
            if joints_destinations[dst]:
                row.append(JOINT_CHOICE_SEPARATOR.join(joints_destinations[dst]))
            else:
                row.append('0')
        # for dst in range(num_states):
        #     if(src == dst):
        #         joint = idle_joint
        #         row.append(joint)
            # # Random decision: include transition or not
            # elif random.random() < sparsity:
            #     # Generate random joint action
            #     joint = AGENT_ACTION_SEPARATOR.join(random.choice(agent_actions) for _ in range(num_agents))
            #     row.append(joint)
            # else:
            #     row.append('0')
        transitions.append(' '.join(row))
    
    #Ensure at least one transition per state to avoid deadlock
    for src in range(num_states):
        row = transitions[src].split()
        if all(cell == '0' for cell in row):
            # Add at least one transition to a random successor
            dst = random.randint(0, num_states - 1)
            # joint = 'AGENT_ACTION_SEPARATOR'.join(random.choice(agent_actions) for _ in range(num_agents))
            joint = idle_joint
            row[dst] = joint
            transitions[src] = ' '.join(row)
    
    # Build unknown transitions (all zeros for simplicity)
    unknown_transitions = [' '.join(['0'] * num_states) for _ in range(num_states)]
    
    # Generate random labelling: each proposition randomly true/false on each state
    labelling = []
    for state_idx in range(num_states):
        row = []
        for prop_idx in range(num_propositions):
            # Bias: ~50% chance of true, but ensure some variation
            row.append('1' if random.random() < 0.5 else '0')
        labelling.append(' '.join(row))
    
    # Build CGS format
    cgs_lines = [
        'Transition',
        *transitions,
        'Unknown_Transition_by',
        *unknown_transitions,
        'Name_State',
        ' '.join(states),
        'Initial_State',
        's0',
        'Atomic_propositions',
        ' '.join(props),
        'Labelling',
        *labelling,
        'Number_of_agents',
        str(num_agents),
        '',  # Trailing newline
    ]
    
    return '\n'.join(cgs_lines)


def save_cgs_to_file(cgs_content: str, filepath: Path | str) -> None:
    """Save CGS model to a file."""
    Path(filepath).write_text(cgs_content, encoding='utf-8')


# def write_random_cgs_file(filepath: Path | str, num_states: int = 4, num_agents: int = 2, num_propositions: int = 1, sparsity: float = 0.5, seed: int | None = None) -> Path:
#     """Generate a random CGS and write it directly to `filepath`.

#     Returns the `Path` to the written file.
#     """
#     p = Path(filepath)
#     cgs_content = generate_random_cgs(num_states=num_states, num_agents=num_agents, num_propositions=num_propositions, sparsity=sparsity, seed=seed)
#     save_cgs_to_file(cgs_content, p)
#     return p


# def save_hardcoded_natatl_file(filepath: Path | str, num_agents: int = 4) -> None:
#     """Write a small set of conservative, hardcoded NatATL formulas to file.

#     The file format is one NatATL formula per line. Lines starting with `#`
#     are treated as comments and ignored by the loader.
#     """
#     samples = [
#         f"<{{1}}, 1>F p",
#         f"<{{1}}, 1>G p",
#         f"<{{1}}, 1>F q",
#         f"<{{1,2}}, 1>p U q",
#         f"<{{1}}, 1>F p | F q",
#         f"<{{1,2}}, 1>F p | F r",
#         f"<{{2}}, 1>G q",
#         f"<{{1}}, 1>p",
#     ]
#     Path(filepath).write_text('\n'.join(samples) + '\n', encoding='utf-8')


#if __name__ == '__main__':
    # # Example usage
    # import sys
    
    # # Generate a random CGS
    # cgs = generate_random_cgs(num_states=5, num_agents=2, num_propositions=2, seed=42)
    # print('Generated CGS:')
    # print(cgs)
    # print('\n' + '='*60 + '\n')
    
#     # Generate test formulas
#     formulas = generate_test_formulas(num_propositions=2)
#     print('Test formulas:')
#     for i, f in enumerate(formulas, 1):
#         print(f'  {i}. {f}')
