import spot

def match_automa(kripke_graph, ltl_formula_str):
    """
    Input:
      - kripke_graph: un oggetto spot.twa_graph (il tuo grafo di test o il CGS convertito)
      - ltl_formula_str: la formula LTL da verificare (es. "F goal")
    Output:
      - Un automa prodotto che contiene i percorsi compatibili
    """
    # 1. Recuperiamo il dizionario esistente dal modello
    b_dict = kripke_graph.get_dict()

    # 2. Traduciamo la formula LTL usando quel dizionario
    try:
        buchi_automa = spot.translate(ltl_formula_str, "small", "buchi", dict=b_dict)
    except Exception as e:
        print(f"Errore nella traduzione della formula: {e}")
        return None

    # 3. Eseguiamo il prodotto (Intersezione)
    # product conterrà solo i cammini del modello che soddisfano la formula
    product = spot.product(kripke_graph, buchi_automa)

    # 4. Controllo se esistono cammini
    if product.is_empty():
        return None

    return product