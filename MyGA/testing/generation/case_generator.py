from pathlib import Path

from MyGA.testing.generation.cgs_generator import generate_random_cgs, save_cgs_to_file
from MyGA.testing.generation.formula_generator import generate_template_natatl_formulas, save_formulas_to_file

def generate_case(
    num_states: int = 4,
    num_agents: int = 2,
    num_aps: int = 4,
    num_agent_actions: int = 3,
    sparsity: float = 0.5,
    coalition_size: int | None = None,
    k : int = 3,
    formula_length: int = 2,
    templates: list[str] | None = None,
    cgs_file: str | Path | None = None,
    formula_file: str | Path | None = None,
    ):
    if cgs_file:
        cgs_content = generate_random_cgs(
            num_states=num_states,
            num_agents=num_agents,
            num_propositions=num_aps,
            num_agent_actions=num_agent_actions,
            sparsity=sparsity
        )
        save_cgs_to_file(cgs_content, cgs_file)

    if formula_file:
        natatl_formulas = generate_template_natatl_formulas(
            num_agents=num_agents,
            coalition_size=coalition_size,
            k=k,
            num_propositions=num_aps,
            set_size=formula_length,
            templates=templates
        )
        save_formulas_to_file(natatl_formulas, formula_file)

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--states', type=int, default=6)
    p.add_argument('--agents', type=int, default=2)
    p.add_argument('--aps', type=int, default=1)
    p.add_argument('--actions', type=int, default=3)
    p.add_argument('--sparsity', type=float, default=0.5)
    p.add_argument('--coalition-size', type=int, default=None, help='If set, use this coalition size for generated NatATL formulas')
    p.add_argument('--k', type=int, default=3, help='The k parameter for generated NatATL formulas')
    p.add_argument('--formula-length', type=int, default=2, help='The number of propositions in each generated NatATL formula')
    p.add_argument('--module-file', type=str, help='Path to a file where the generated CGS will be saved')
    p.add_argument('--formula-file', type=str, help='Path to a file where the generated NatATL formulas will be saved')
    args = p.parse_args()

    generate_case(
        num_states=args.states,
        num_agents=args.agents,
        num_aps=args.aps,
        num_agent_actions=args.actions,
        sparsity=args.sparsity,
        coalition_size=args.coalition_size,
        k=args.k,
        formula_length=args.formula_length,
        cgs_file=args.module_file,
        formula_file=args.formula_file
    )

