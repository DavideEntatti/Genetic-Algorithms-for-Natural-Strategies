import spot

# def evaluate(wrong_model, right_model, deadlocks):
#     return evalueate_wrong(wrong_model, deadlocks) - evaluate_right(right_model)

def evalueate_right(model):
    mapping = model.get_product_states()
    sccs = spot.scc_info(model)
    is_good = [sccs.is_accepting_scc(sccs.scc_of(i)) for i in range(model.num_states())]

    changed = True
    while changed:
        changed = False
        for s in range(model.num_states()):
            if not is_good[s]:
                if all(is_good[edge.dst] for edge in model.out(s)):
                    changed = True
                    is_good[s] = True

    right_paths = 0
    # for s in range(model.num_states()):
    BFS_Queue = [model.get_init_state_number()]
    visited = []
    while BFS_Queue:
        s = BFS_Queue.pop(0)
        visited.append(s)
    #     # Uso un set perchè nel prodotto gli archi possono comparire più volte
        d_nodes = set()

        for edge in model.out(s):
            # Uso dst_id per il nodo del cgs, mentre uso edge.dst per lo stato del prodotto
            #src_id = mapping[edge.src][0]
            if edge.dst in visited:
                continue
            BFS_Queue.append(edge.dst)
            dst_id = mapping[edge.dst][0]
            if is_good[edge.src] and is_good[edge.dst]:
                d_nodes.add(dst_id)
        n = len(d_nodes)
        if n == 1:
            right_paths += 0.2
        if n > 1:
            #n-1 per non tenere conto del cammino corrente
            right_paths += (n-1)
    
    #Aggiunto per tutte le strategie soddisfacienti
    if is_good[model.get_init_state_number()]:
        right_paths += 1

    return right_paths

def evalueate_wrong(model, deadlocks):
    # Ottnego gli stati del grafo kripke a cui corrispondono gli stati del prodotto
    mapping = model.get_product_states()

    # if model.is_empty():
    #     return 0

    # Vengono segnati come "bad" gli stati che fanno parte di una SCC accettante
    sccs = spot.scc_info(model)
    # `sccs.is_accepting_scc` prende un indice di SCC, non di stato. Qui mappiamo
    # ogni stato al suo indice di SCC tramite `sccs.scc_of(state)`.

    #with open("sccs.txt", "w") as f:
    #     f.write("ALL TRANSITIONS")
    #     for s in range(model.num_states()):
    #         f.write(f"\nSTATE: {s}, MAPPING: {mapping[s][0]},{mapping[s][1]}\n")
    #         for out in model.out(s):
    #             f.write(f"{out.dst}, ")

    #f.write("\n")
    is_bad = [sccs.is_accepting_scc(sccs.scc_of(i)) for i in range(model.num_states())]

    # for s in range(model.num_states()):
    #     f.write(f"State {s}: SCC {sccs.scc_of(s)}, Accepting: {is_bad[s]}\n")

    # for s in range(model.num_states()):
    #     if s == mapping[s][0]:  # Solo gli stati del CGS
    #         has_out = any(True for _ in model.out(s))
    #         if not has_out:
    #             is_bad[s] = True
    #             for p in range(model.num_states()):
    #                 if mapping[p][0] == s:
    #                     is_bad[p] = True  # Stati del CGS in altri stati del prodotto

    # for s in range(model.num_states()):
    #     if is_bad[s]:
    #         f.write(f"State {s} is bad after scc control\n")

    for d in deadlocks:
        for s in range(model.num_states()):
            if mapping[s][0] == d:
                is_bad[s] = True
                #f.write(f"State {s} is bad because of recognised deadlock in CGS state {d}\n")
                # if s in deadlocks:
                #     for p in range(model.num_states()):
                #         if mapping[p][0] == s:
                #             is_bad[p] = True
                #             f.write(f"State {p} is bad because of recognised deadlock in CGS state {s}\n")

    #Tutti sli stati che portano verso uno stato "bad" vengono segnati come "bad"
    changed = True
    while changed:
        changed = False
        for s in range(model.num_states()):
            if not is_bad[s]:
                for edge in model.out(s):
                    if is_bad[edge.dst]:
                        changed = True
                        is_bad[s] = True
                        break

    # for s in range(model.num_states()):
    #     if is_bad[s]:
    #         f.write(f"State {s} is bad after propagation\n")

    #Calcoliamo il numero di cammini nelle regioni bad (usiamo le biforcazioni)
    wrong_paths = 0
    # for s in range(model.num_states()):
    BFS_Queue = [model.get_init_state_number()]
    visited = []
    while BFS_Queue:
        s = BFS_Queue.pop(0)
        visited.append(s)
    #     # Uso un set perchè nel prodotto gli archi possono comparire più volte
        d_nodes = set()
        # `model.out(s)` è un oggetto iterabile che può risultare Truthy anche se vuoto,
        # quindi verifichiamo l'assenza di archi esplicitamente.
        # has_out = any(True for _ in model.out(s))
        # if not has_out:
        #     wrong_paths += 1
        for edge in model.out(s):
            # Uso dst_id per il nodo del cgs, mentre uso edge.dst per lo stato del prodotto
            #src_id = mapping[edge.src][0]
            if edge.dst in visited:
                continue
            BFS_Queue.append(edge.dst)
            dst_id = mapping[edge.dst][0]
            if is_bad[edge.src] and is_bad[edge.dst]:
                d_nodes.add(dst_id)
        n = len(d_nodes)
        if n == 1:
            wrong_paths -= 0.2
        elif n > 1:
            #n-1 per non tenere conto del cammino corrente
            wrong_paths += (n-1)
    
    #Aggiunto per tutte le strategie non soddisfacienti
    if is_bad[model.get_init_state_number()]:
        wrong_paths += 1

    return wrong_paths