from model_checker.algorithms.explicit.NatATL.Memoryless.NatATL import model_checking
#from model_checker.benchmarking.adapters import get_model_checker

def run_vitamin(formula, path):

    # Run the Vitamin NatATL model checker on the given formula and model path.
    res = None
    try:
        res = model_checking(formula, path)
        #checker = get_model_checker('NatATL')
        #res = checker(natatl_formula, str(model_path))
    except Exception as e:
        status = None
        res = f'ERROR: {e}'
    try:
        if isinstance(res, dict):
            if res.get('Satisfiability') is True:
                status= True
            elif 'Winning Strategy' in repr(res) or 'Winning Strategy per agent' in repr(res):
                status = True
            elif isinstance(res.get('res', None), str) and res.get('res').startswith('Result: True'):
                status = True
            else:
                status = False
    except Exception:
        status = False
    return status, repr(res)

#Calling the model checker through the benchmark funtionality (commented code) has the same behaviuor