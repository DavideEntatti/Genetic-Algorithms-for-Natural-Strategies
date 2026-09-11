from typing import List
from pathlib import Path

# def generate_test_formulas(num_propositions: int = 1) -> List[str]:
#     """Generate a set of test LTL formulas.
    
#     Args:
#         num_propositions: Number of atomic propositions in the model
        
#     Returns:
#         List of LTL formulas to test
#     """
#     props = [chr(ord('p') + i) for i in range(num_propositions)]
    
#     formulas = []
    
#     # Basic formulas
#     for prop in props:
#         formulas.append(prop)  # p
#         formulas.append(f'!{prop}')  # !p
#         formulas.append(f'F {prop}')  # eventually p
#         formulas.append(f'G {prop}')  # globally p
#         formulas.append(f'G !{prop}')  # globally not p
    
#     # Compound formulas
#     if len(props) >= 2:
#         p, q = props[0], props[1]
#         formulas.extend([
#             f'{p} || {q}',  # p or q
#             f'{p} && {q}',  # p and q
#             f'F ({p} && {q})',  # eventually both
#             f'G ({p} || {q})',  # always at least one
#             f'{p} U {q}',  # p until q
#             f'G (F {p})',  # infinitely often p
#             f'F (G {p})',  # eventually always p
#         ])
    
#     # Remove duplicates while preserving order
#     seen = set()
#     unique_formulas = []
#     for f in formulas:
#         if f not in seen:
#             seen.add(f)
#             unique_formulas.append(f)
    
#     return unique_formulas


# def generate_natatl_formulas(
#     num_agents: int,
#     coalition_size: int | None = None,
#     num_propositions: int = 1,
#     seed: int | None = None,
#     force_wrapper_only: bool = False,
# ) -> List[str]:
#     """Generate NatATL formulas with randomized coalitions.

#     Each returned string is a NatATL-style formula with a leading coalition
#     marker like "<{1,3}, 1>F p". The underlying LTL formulas are produced by
#     `generate_test_formulas` and the coalition members are chosen uniformly at
#     random among agents (1-based indices).

#     Args:
#         num_agents: total number of agents in the CGS
#         coalition_size: number of agents in the coalition; if None, choose a
#             random size between 1 and num_agents-1 for each formula
#         num_propositions: number of atomic propositions (passed to LTL generator)
#         seed: optional random seed for reproducibility

#     Returns:
#         List of NatATL formula strings.
#     """
#     # Deprecated: original generator implementation commented out. Use the
#     # template-based generator `generate_template_natatl_formulas` instead.
#     # The wrapper below preserves the original API for compatibility.
#     return generate_template_natatl_formulas(
#         num_agents=num_agents,
#         coalition_size=coalition_size,
#         num_propositions=max(1, num_propositions),
#         seed=seed,
#     )


def _build_prop_set(props: list[str], set_size: int, true_ratio: float = 0.5, style: str = 'mixed') -> str:
    """Build a set-expression over atomic props.

    - props: list of proposition names
    - set_size: number of props to include in the set
    - true_ratio: fraction of chosen props to be positive (rest negated)
    - style: 'conj'|'disj'|'mixed' join operator
    """
    import random

    candidates = list(props)
    if set_size <= 0:
        return "True"
    chosen = random.sample(candidates, k=min(set_size, len(candidates)))
    n_true = max(1, int(round(len(chosen) * true_ratio)))
    positives = set(chosen[:n_true])
    atoms = []
    for p in chosen:
        atom = p if p in positives else f'!{p}'
        atoms.append(atom)

    if style == 'conj':
        return ' && '.join(atoms)
    if style == 'disj':
        return ' || '.join(atoms)
    # mixed: randomly choose between && and ||
    expr = atoms[0]
    for a in atoms[1:]:
        op = random.choice([' && ', ' || '])
        expr = f'({expr}{op}{a})'
    return expr


def generate_template_natatl_formulas(
    num_agents: int,
    coalition_size: int | None = None,
    k : int = 3,
    num_propositions: int = 2,
    seed: int | None = None,
    templates: list[str] | None = None,
    set_size: int = 1,
    true_ratio: float = 0.5,
) -> List[str]:
    """Generate NatATL formulas from scalable templates.

    templates: subset of ['X', 'U','F','G'] to generate. Defaults to first
    five templates.
    """
    if seed is not None:
        import random

        random.seed(seed)

    if templates is None:
        templates = ['X','F','G','U']

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
    
    natatl_list: List[str] = []

    # For each template create one formula (can be extended to multiple)
    # pick coalition members randomly per formula
    import random

    for templ in templates:
        # coalition
        if coalition_size is None:
            size = random.randint(1, max(1, num_agents - 1))
        else:
            size = max(1, min(coalition_size, num_agents))
        members = random.sample(list(range(1, num_agents + 1)), k=size)
        members_str = ','.join(str(m) for m in sorted(members))

        # build sets: each set is homogeneous (only conjunctions OR only disjunctions)
        if templ == 'U':
            left = _build_prop_set(props, set_size, true_ratio, style='disj')
            right = _build_prop_set(props, set_size, true_ratio, style='conj')
            formula = f"({left}) U ({right})"
        elif templ == 'F':
            left = _build_prop_set(props, set_size, true_ratio, style='conj')
            formula = f"F ({left})"
        elif templ == 'X':
            left = _build_prop_set(props, set_size, true_ratio, style='disj')
            formula = f"X ({left})"
        elif templ == 'G':
            left = _build_prop_set(props, set_size, true_ratio, style='disj')
            formula = f"G ({left})"
        else:
            left = _build_prop_set(props, set_size, true_ratio, style='disj')
            formula = f"{templ}({left})"


        #k = random.randint(coalition_size*2, coalition_size*4)  # Random k between coalition size and total agents

        natatl = "<{" + members_str + "}, " + str(k) + ">" + formula
        natatl_list.append(natatl)

    return '\n'.join(natatl_list)

def save_formulas_to_file(cgs_content: str, filepath: Path | str) -> None:
    """Write NatATL formulas to file."""
    Path(filepath).write_text(cgs_content, encoding='utf-8')