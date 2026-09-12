from MyGA.model_checking.LTL_cheking import match_automa
from MyGA.model_checking.model_evaluation import evalueate_right, evalueate_wrong
from MyGA.strategy.strategy import Strategy
from MyGA.evolution.crossing_over import new_population, new_generation
from MyGA.models.cgs.cgs_functions import prune, cgs_to_kripke, complete, read_CGS
from MyGA.models.formula.fromula_functions import NatATL_formula_info
from MyGA.config import config
import spot

def search_strategy(formula, model_path):
    cgs, agents_actions, aps = read_CGS(model_path)
    formula, coalition, k = NatATL_formula_info(formula)

    # out = "gen.txt"
    # with open(out, 'w') as f:
    # f.write(str(k))
    # f.write(formula)
    b_dict = spot.make_bdd_dict()
    kripke_graph = cgs_to_kripke(cgs, b_dict)
    neg_formula = "!("+formula+")"
    #wrong = match_automa(kripke_graph, neg_formula)
    right = match_automa(kripke_graph, formula)

    # agenti della coalizione — reindicizziamo i set di azioni in modo che
    # vadano da 0..m-1 (m = numero di agenti nella coalizione). Questo evita
    # KeyError quando `Strategy.randomize` si aspetta indici compatti.
    #coalition_indices = [i for i, in_coal in enumerate(coalition_agents) if in_coal]
    active_agents_actions = {new_i: agents_actions[old_i] for new_i, old_i in enumerate(coalition)}

    if not right:
        #print("No Strategy")
        return "No solution", None
    # elif not wrong:
    #     #print("Any Strategy")
    #     return "Any solution", None
    k_solution = float("inf")
    solution = None
    # f.write("ALL KRIPKE TRANSITIONS")
    # for s in range(kripke_graph.num_states()):
    #     f.write(f"\nSTATE: {s}\n")
    #     for out in kripke_graph.out(s):
    #         f.write(f"{out.dst}, ")
    # f.write("\nALL WRONG TRANSITIONS")
    # for s in range(wrong.num_states()):
    #     f.write(f"\nSTATE: {s}\n")
    #     for out in wrong.out(s):
    #         f.write(f"{out.dst}, ")
    # f.write("\nALL RIGHT TRANSITIONS")
    # for s in range(right.num_states()):
    #     f.write(f"\nSTATE: {s}\n")
    #     for out in right.out(s):
    #         f.write(f"{out.dst}, ")
    #f.write("\n")

    population = new_population(config.POPULATION_SIZE, active_agents_actions, aps, k)
    found_new_solution = False
    k_iter = 0
    #good_strategies = 0
    while (k_iter < config.DYNAMIC_K or k_iter == 0):
        i = 0
        while i < config.MAX_GENERATIONS:
            fit_tot = 0
            #f.write(f"GEN: {i}\n")
            found_new_solution = False
            for idx in range(len(population)):
                if population[idx][1]:  # fitness = None per individui non valutati
                    if population[idx][1] != float('inf'):
                        fit_tot += population[idx][1]
                else:
                    strategy = population[idx][0]
                        # if(strategy.agents[0].get_k() == 0 and strategy.agents[1].get_k() == 0):
                        #     good_strategies += 1
                    if strategy.get_k() > k:
                        print(f"HUH{k}")
                    # model pruning e traduzione
                    pruned_cgs = prune(cgs, strategy, coalition)
                    model = cgs_to_kripke(pruned_cgs, b_dict)
                    deadlocks = complete(model)
                    #print(deadlocks)
                    # f.write(f"\nSTRATEGY: {strategy.get_strategy()}")
                    # f.write("\nALL PRUNED TRANSITIONS")
                    # for s in range(model.num_states()):
                    #     f.write(f"\nSTATE: {s}\n")
                    #     for out in model.out(s):
                    #         f.write(f"{out.dst}, ")
                    #model_checking
                    pruned_right = match_automa(model, formula)
                    pruned_wrong = match_automa(model, neg_formula)
                    if pruned_wrong:
                        # product = spot.product(model, pruned_wrong)
                        # if product:
                        # f.write("\nALL WRONG TRANSITIONS")
                        # for s in range(pruned_wrong.num_states()):
                        #     f.write(f"\nSTATE: {s}\n")
                        #     for out in pruned_wrong.out(s):
                        #         f.write(f"{out.dst}, ")
                        # f.write("\n")
                        fitness = evalueate_wrong(pruned_wrong, deadlocks) #+ len(deadlocks)
                        if pruned_right:
                            fitness -= evalueate_right(pruned_right)
                        fit_tot += fitness
                        population[idx] = (Strategy.copy(population[idx][0]), fitness)
                        # f.write(f"STRATEGY: {strategy.get_strategy()}")
                        # f.write(f"FITNESS: {fitness}\n")
                        # f.write(f"K: {strategy.get_k()}\n")
                    else:
                        # product empty -> strategy satisfies formula
                        # Reject strategies that deadlock the initial state
                        # try:
                        #     init_idx = cgs.states.index(cgs.initial_state) if hasattr(cgs, 'states') else 0
                        # except Exception:
                        #     init_idx = 0
                        # pruned_row = pruned_cgs.graph[init_idx]
                        # if all(cell == 0 for cell in pruned_row):
                        #     # mark this individual as evaluated with worst fitness and continue
                        #     population[idx] = (Strategy.copy(population[idx][0]), float('inf'))
                        #     fit_tot += float('inf')
                        #     continue
                        #print("\nCheck:\n")
                        if pruned_right.accepting_run():
                            if config.DYNAMIC_K == 0:
                                found_new_solution = True
                                solution = strategy
                                break
                            strat_k = strategy.get_k()
                            if(strat_k<k_solution):
                                found_new_solution = True
                                solution = strategy
                                k_solution = strat_k
                        else:
                            print("BRUH")
                            if fitness == 0:
                                print("WHY?")
                            # population[idx] = (Strategy.copy(population[idx][0]), float('inf'))
                            #fit_tot += float('inf')
                            
            #avg_denom = max(1, len(population))
            #print(f"Average fitness:{fit_tot/avg_denom}")

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


    # print(f"Good strategies: {good_strategies}")
    if solution:
        return "Found", solution
    else:
        return "Failure", None