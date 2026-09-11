import streamlit as st
from pyvis.network import Network
import networkx as nx
import os

from MyGA.testing.running.case_runner import run_case
from MyGA.web_app.display_cgs import display_CGS
from MyGA.models.formula.fromula_functions import NatATL_formula_info
from MyGA.config import config

temp_path = "MyGA/web_app/temp"

# 1. Configurazione della pagina (Wide mode per usare tutto lo schermo)
st.set_page_config(layout="wide", page_title="CGS Visualizer")

st.title("NatATL verification with genetic algorithm")

# --- INIZIALIZZAZIONE MEMORIA ---
if 'cgs_path' not in st.session_state:
    st.session_state['cgs_path'] = None
if 'formula_path' not in st.session_state:
    st.session_state['formula_path'] = None
if 'result' not in st.session_state:
    st.session_state['result'] = None
if 'formula_info' not in st.session_state:
    st.session_state['formula_info'] = None

# 2. TAB Superiori
tab1, tab2= st.tabs(["Find Strategy", "GA Configuration"])

with tab1:
    # Creiamo due colonne principali: Sinistra (Grafo) e Destra (Parametri)
    col_left, col_right = st.columns([2, 1]) # La colonna sinistra è il doppio della destra

    # --- COLONNA DESTRA ---
    with col_right:
        # Tasto Caricamento File (in alto a destra)
        st.write("📁 **Load Model**")
        uploaded_file = st.file_uploader("Drag CGS file here", type=["txt"])

        if uploaded_file:
            file = os.path.join(os.getcwd(), temp_path+'/temp_'+uploaded_file.name)
            if file != st.session_state['cgs_path']:
                st.session_state['result'] = None
                st.session_state['cgs_path'] = file
                with open(file, "wb") as f:
                    f.write(uploaded_file.getbuffer())


        # Formula (Finestra interattiva)
        st.subheader("NatATL Formula")
        formula = st.text_input("Write formula here:")
        if formula:
            st.session_state['formula_info'] = NatATL_formula_info(formula)
            file = os.path.join(os.getcwd(), temp_path+'/temp_formula.txt')
            st.session_state['formula_path'] = file
            with open(file, "w") as f:
                f.write(formula)
        #st.info(f"Formula attuale: {formula}")

        # Area Strategia Trovata (sotto il grafo)
        st.subheader("Strategia Trovata")
        strategy_box = st.container(border=True)
        with strategy_box:
            if st.session_state['result']:
                if st.session_state['result'][0] == 'Found':
                    st.code(st.session_state['result'][1].get_strategy(coalition = st.session_state['formula_info'][1]))
                else: 
                    st.code(st.session_state['result'][0])

        time_box = st.container(border=True)
        with time_box:
            if st.session_state['result']:
                st.code("Execution Time: "+str(st.session_state['result'][2]))


        # Spazio vuoto per estetica
        st.write("---")

        # Tasto Avvio (in basso)
        if st.button("START ALGORITHM", use_container_width=True, type="primary"):
            if st.session_state['cgs_path'] and st.session_state['formula_path']:
                with st.spinner("Executing GA..."):
                    # Qui chiamerai la tua funzione ga.run()
                    st.session_state['result'] = run_case(st.session_state['cgs_path'], st.session_state['formula_path'], vitamin=False, ga=True)['ga'][0]
                    st.rerun()

        

    # --- COLONNA SINISTRA ---
        with col_left:
            st.subheader("CGS graph visualization")
            
            # Area per il Grafo (utilizziamo un container con bordo)
            graph_container = st.container(border=True, height='stretch')
            with graph_container:
                # Creazione di un grafo d'esempio con Pyvis
                net = Network(height="720px", width="100%", directed=True, bgcolor="#ffffff")
                if st.session_state['cgs_path']:
                    if st.session_state['result'] and st.session_state['result'][0] == 'Found':
                        G = display_CGS(st.session_state['cgs_path'], st.session_state['result'][1], st.session_state['formula_info'])
                    else:
                        G = display_CGS(st.session_state['cgs_path'])
                    net.from_nx(G)
                    net.set_options("""
                    {
                    "interaction": {
                        "navigationButtons": true,
                        "hover": true,
                        "keyboard": true
                    },
                    "physics": {
                        "barnesHut": {
                        "gravitationalConstant": -50000,
                        "centralGravity": 0.3,
                        "springLength": 250,
                        "springConstant": 0.001,
                        "damping": 0.09,
                        "avoidOverlap": 1
                        },
                        "solver": "barnesHut",
                        "stabilization": {
                        "enabled": true,
                        "iterations": 1000
                        }
                    },
                    "edges": {
                        "smooth": {
                        "type": "curvedCW",
                        "roundness": 0.3
                        }
                    }
                    }
                    """)
                
                # Generazione HTML del grafo
                path = temp_path+'/temp_graph.html'
                net.save_graph(path)
                with open(path, 'r', encoding='utf-8') as f:
                    import streamlit.components.v1 as components
                    components.html(f.read(), height=720)
            
with tab2:
    #Slider e altri Setting
    st.subheader("GA configuration")
    settings_box = st.container(border=True)
    with settings_box:
        pop_size = st.number_input("Population Size", 1, 500, config.POPULATION_SIZE)
        generations = st.number_input("Generations", 1, 1000, config.MAX_GENERATIONS)
        elite = st.number_input("Elites", 0, 50, config.N_ELITE)
        extra = st.number_input("Extras", 0, 50, config.EXTRA_STRATEGIES)
        tournament = st.number_input("Tournament Size", 0, 50, config.TOURNAMENT_SIZE)
        order_mut = st.slider("Order mutation Rate", 0.0, 1.0, config.ORDER_MUTATION)
        action_mut = st.slider("Action mutation Rate", 0.0, 1.0, config.ACTION_MUTATION)
        cond_mut = st.slider("Condition mutation Rate", 0.0, 1.0, config.CONDITION_MUTATION)
        dyn_k = st.number_input("Dynamic_k", 0, 10, config.DYNAMIC_K)
        if st.button("APPLY", use_container_width=True, type="primary"):
            config.set_config(pop_size, generations, elite, extra, tournament, order_mut, action_mut, cond_mut, dyn_k)

