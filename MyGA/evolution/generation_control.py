from MyGA.model_checking.LTL_cheking import match_automa
from MyGA.model_checking.model_evaluation import evalueate_right, evalueate_wrong
from MyGA.strategy.strategy import Strategy
from MyGA.evolution.crossing_over import new_population, new_generation
from MyGA.models.cgs.cgs_functions import prune, cgs_to_kripke, complete, read_CGS
from MyGA.models.formula.fromula_functions import NatATL_formula_info
from MyGA.config import config
from math import sqrt
import spot


def search_strategy(formula, model_path, csv_buffer=None):
    cgs, agents_actions, aps = read_CGS(model_path)
    formula, coalition, k = NatATL_formula_info(formula)

    if config.DYNAMIC_SETTINGS:                                                                                                                                               
        max_actions = max(len(a) for a in agents_actions.values()) if agents_actions else 2                                                                                   
        c_size = len(coalition)                                                                                                                                               
                                                                                                                                                                                
        # Crescita sub-lineare/controllata per evitare esplosioni                                                                                                             
        pop_size = int(max(30, min(80, 25 + 10 * c_size + 4 * k)))                                                                                                            
        gens = int(max(20, min(45, 15 + 4 * k + 2 * len(aps))))                                                                                                               
                                                                                                                                                                                
        # 1 o 2 élite bastano per non perdere la soluzione migliore                                                                                                           
        elites = max(1, int(pop_size * 0.05))       # 5% (es. 2-4 individui)                                                                                                  
        extras = max(1, int(pop_size * 0.05))       # 5% per diversità controllata                                                                                            
        tournament = max(2, min(5, int(pop_size * 0.05))) # Torneo tra 2 e 5                                                                                                  
                                                                                                                                                                                
        config.set_config(pop_size=pop_size, gens=gens, elites=elites, extras=extras, tournament=tournament)

    b_dict = spot.make_bdd_dict()
    kripke_graph = cgs_to_kripke(cgs, b_dict)
    neg_formula = "!("+formula+")"
    buchi_right = spot.translate(formula, "small", "buchi", dict=b_dict)
    buchi_wrong = spot.translate(neg_formula, "small", "buchi", dict=b_dict)

    if not buchi_right or spot.product(kripke_graph, buchi_right).is_empty():
        return "No solution", None

    # agenti della coalizione — reindicizziamo i set di azioni in modo che
    # vadano da 0..m-1 (m = numero di agenti nella coalizione). Questo evita
    # KeyError quando `Strategy.randomize` si aspetta indici compatti.
    #coalition_indices = [i for i, in_coal in enumerate(coalition_agents) if in_coal]
    active_agents_actions = {new_i: agents_actions[old_i] for new_i, old_i in enumerate(coalition)}

    # Pre-calcolo delle proposizioni atomiche attive per ogni stato del CGS
    atomic_props_list = [str(p) for p in cgs.atomic_propositions]
    state_active_props = [
        [atomic_props_list[p_idx] for p_idx, val in enumerate(cgs.matrix_prop[s_idx]) if val == 1]
        for s_idx in range(len(cgs.graph))
    ]

    k_solution = float("inf")
    solution = None

    population = new_population(config.POPULATION_SIZE, active_agents_actions, aps, k)
    found_new_solution = False
    k_iter = 0
    while (k_iter < config.DYNAMIC_K or k_iter == 0):
        i = 0
        while i < config.MAX_GENERATIONS:
            fit_tot = 0
            found_new_solution = False
            for idx in range(len(population)):
                if population[idx][1] is not None:  # fitness = None per individui non valutati
                    fit_tot += population[idx][1] #Add elites fitness to total
                else:
                    strategy = population[idx][0]

                    if strategy.get_k() > k:
                        print(f"HUH{k}")
                    # model pruning e traduzione
                    pruned_cgs = prune(cgs, strategy, coalition, state_active_props)
                    model = cgs_to_kripke(pruned_cgs, b_dict)
                    deadlocks = complete(model)
                    #model_checking
                    pruned_right = spot.product(model, buchi_right)
                    pruned_wrong = spot.product(model, buchi_wrong)
                    right_empty = pruned_right.is_empty()
                    wrong_empty = pruned_wrong.is_empty()

                    fitness = 0
                    if not right_empty:
                        fitness -= evalueate_right(pruned_right)
                    if not wrong_empty:
                        fitness += evalueate_wrong(pruned_wrong, deadlocks) #+ len(deadlocks)

                    fit_tot += fitness
                    population[idx] = (population[idx][0], fitness)


                    if wrong_empty and not right_empty:
                        if pruned_right.accepting_run():
                            if config.DYNAMIC_K == 0:
                                found_new_solution = True
                                solution = strategy
                            strat_k = strategy.get_k()
                            if(strat_k<k_solution):
                                found_new_solution = True
                                solution = strategy
                                k_solution = strat_k
                        else:
                            print("BRUH")
                            if fitness == 0:
                                print("WHY?")
                            
            avg_denom = max(1, len(population))
            average_fitness = fit_tot/avg_denom

            if csv_buffer:
                row = {"Gen":i,"Fit":average_fitness,"Sol":found_new_solution}
                csv_buffer.add_row(row)

            if found_new_solution:
                break

            population.sort(key=lambda x: x[1])
            population = new_generation(population, active_agents_actions, aps, k)

            i += 1

        if  found_new_solution and config.DYNAMIC_K != 0:
            k=k_solution-1
            population = new_generation(population, active_agents_actions, aps, k, elite=False)
        elif config.DYNAMIC_K != 0:
            k+=1
            population = new_generation(population, active_agents_actions, aps, k)

        if not found_new_solution and solution:
            break
        k_iter += 1

    if solution:
        return "Found", solution
    else:
        return "Failure", None