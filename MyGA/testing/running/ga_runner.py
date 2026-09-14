from MyGA.evolution.generation_control import search_strategy

def run_ga(formula, model_path):
    #Run the Genetic Algorithm
    res = None
    try:
        status, res = search_strategy(formula, model_path)
    except Exception as e:                
        res = f'ERROR: {e}'
        print(e)
        status = None
    if type(res) == str:
        return status, res
    elif res:
        return status, res
    else:
        return status, None