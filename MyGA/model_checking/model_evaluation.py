from collections import deque
import spot

# def evaluate(wrong_model, right_model, deadlocks):
#     return evalueate_wrong(wrong_model, deadlocks) - evaluate_right(right_model)

def evalueate_right(model):
    mapping = model.get_product_states()
    num_states = model.num_states()
    sccs = spot.scc_info(model)
    is_good = [sccs.is_accepting_scc(sccs.scc_of(i)) for i in range(num_states)]

    changed = True
    while changed:
        changed = False
        for s in range(num_states):
            if not is_good[s]:
                if all(is_good[edge.dst] for edge in model.out(s)):
                    changed = True
                    is_good[s] = True

    right_paths = 0
    init_state = model.get_init_state_number()
    BFS_Queue = deque([init_state])
    enqueued = {init_state}
    visited = set()
    while BFS_Queue:
        s = BFS_Queue.popleft()
        visited.add(s)
        d_nodes = set()

        for edge in model.out(s):
            if edge.dst in visited:
                continue
            if edge.dst not in enqueued:
                enqueued.add(edge.dst)
                BFS_Queue.append(edge.dst)
            dst_id = mapping[edge.dst][0]
            if is_good[edge.src] and is_good[edge.dst]:
                d_nodes.add(dst_id)
        n = len(d_nodes)
        if n == 1:
            right_paths += 0.2
        elif n > 1:
            #n-1 per non tenere conto del cammino corrente
            right_paths += (n-1)
    
    #Aggiunto per tutte le strategie soddisfacienti
    if is_good[init_state]:
        right_paths += 1

    return right_paths

def evalueate_wrong(model, deadlocks):
    # Ottengo gli stati del grafo kripke a cui corrispondono gli stati del prodotto
    mapping = model.get_product_states()
    num_states = model.num_states()

    # Vengono segnati come "bad" gli stati che fanno parte di una SCC accettante
    sccs = spot.scc_info(model)
    is_bad = [sccs.is_accepting_scc(sccs.scc_of(i)) for i in range(num_states)]

    deadlocks_set = set(deadlocks)
    if deadlocks_set:
        for s in range(num_states):
            if mapping[s][0] in deadlocks_set:
                is_bad[s] = True

    # Tutti gli stati che portano verso uno stato "bad" vengono segnati come "bad"
    # Propagazione backward O(V + E)
    in_edges = [[] for _ in range(num_states)]
    for s in range(num_states):
        for edge in model.out(s):
            in_edges[edge.dst].append(s)

    bad_queue = deque([s for s in range(num_states) if is_bad[s]])
    while bad_queue:
        curr = bad_queue.popleft()
        for prev in in_edges[curr]:
            if not is_bad[prev]:
                is_bad[prev] = True
                bad_queue.append(prev)

    # Calcoliamo il numero di cammini nelle regioni bad (usiamo le biforcazioni)
    wrong_paths = 0
    init_state = model.get_init_state_number()
    BFS_Queue = deque([init_state])
    enqueued = {init_state}
    visited = set()
    while BFS_Queue:
        s = BFS_Queue.popleft()
        visited.add(s)
        d_nodes = set()
        for edge in model.out(s):
            if edge.dst in visited:
                continue
            if edge.dst not in enqueued:
                enqueued.add(edge.dst)
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
    
    # Aggiunto per tutte le strategie non soddisfacienti
    if is_bad[init_state]:
        wrong_paths += 1

    return wrong_paths