from typing import List
from pathlib import Path

def load_natatl_formulas(filepath: Path | str) -> List[str]:
    """Load NatATL formulas from a file, ignoring blank lines and comments.

    Returns a list of formula strings (stripped).
    """
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"Formulas file not found: {filepath}")
    lines = p.read_text(encoding='utf-8').splitlines()
    formulas: List[str] = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        formulas.append(s)
    return formulas

def NatATL_formula_info(formula: str):
    """Extract information from a NatATL formula string.
    """
    ltl_formula = None
    coalition_agents_local = []
    s = formula.strip()
    if s.startswith('<'):
        end = s.find('>')
        if end != -1:
            marker = s[1:end].strip()
            import re
            nums = [int(n) for n in re.findall(r"\d+", marker)]
            if nums:
                if len(nums) == 1:
                    # single number: treat as both agent and bound
                    a_nums = [nums[0]]
                    k= nums[0]
                else:
                    a_nums = nums[:-1]
                    k = nums[-1]
                for n in a_nums:
                    idx = int(n) - 1
                    coalition_agents_local.append(idx)
            ltl_formula = s[end + 1 :].strip()
    return ltl_formula, coalition_agents_local, k
