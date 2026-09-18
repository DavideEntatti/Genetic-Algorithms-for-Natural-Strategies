import streamlit as st
from pyvis.network import Network
import networkx as nx
import os
from pathlib import Path
import shutil
import psutil
import multiprocessing

from MyGA.testing.benchmark import run_benchmark
from MyGA.testing.plot_drawer import draw_plot, get_keys_and_results
from MyGA.testing.running.case_runner import run_case
from MyGA.web_app.display_cgs import display_CGS
from MyGA.web_app.profiles import add_profile_dialog, edit_profile_dialog, load_benchmark_profiles, save_profile_to_disk, zip_folder
from MyGA.models.formula.fromula_functions import NatATL_formula_info
from MyGA.config import config

temp_path = "MyGA/web_app/temp"
folder = Path(temp_path)
folder.mkdir(parents=True, exist_ok=True)

# 1. Configurazione della pagina (Wide mode per usare tutto lo schermo)
st.set_page_config(layout="wide", page_title="Genetic NatATL")

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

# Gestione sessione per i profili caricati da disco
if 'benchmark_profiles' not in st.session_state or st.session_state['benchmark_profiles'] is None:
    st.session_state['benchmark_profiles'] = load_benchmark_profiles()
    # Se non ci sono profili, creiamo un default di esempio
    if not st.session_state['benchmark_profiles']:
        default_data = {
            "benchmark_metadata": {
                "name": "Default Benchmark",
                "description": "A benchmark for testing the genetic algorithm with default settings."
            },
            "execution": {
                "ga": 1, "vitamin": 1, "mixed": 1, "timeout": 120,
                "directory": "MyGA/web_app/temp/profile_1",
                "benchmark_output": "MyGA/web_app/temp/profile_1/output/benchmark_output.csv"
            },
            "start_parameters": {
                "num_states": 4, "num_agents": 2, "num_agent_actions": 2,
                "num_aps": 3, "sparsity": 0.5, "coalition_size": 1, "k": 1, "set_size": 3
            },
            "execution_plan": {
                "iterations_per_config": 5, "num_configs": 6,
                "final_values": {
                    "fin_num_states": 9, "fin_num_agents": 4, "fin_num_agent_actions": 4,
                    "fin_num_aps": 6, "fin_sparsity": 0.5, "fin_coalition_size": 2, "fin_k": 1, "fin_set_size": 3
                }
            },
            "template_parameters": {
                "templates": ["G", "F", "X", "U"],
                "template_repetitions": 6
            }
        }
        save_profile_to_disk(1, default_data)
        st.session_state['benchmark_profiles'] = load_benchmark_profiles()

if 'editing_profile_id' not in st.session_state:
    st.session_state['editing_profile_id'] = None
if 'show_add_form' not in st.session_state:
    st.session_state['show_add_form'] = False
if 'running_processes' not in st.session_state:
    st.session_state['running_processes'] = {}

if st.session_state.get('show_add_form', False):
    add_profile_dialog()
elif st.session_state.get('editing_profile_id') is not None:
    edit_profile_dialog(st.session_state['editing_profile_id'])

# 2. TAB Superiori
tab1, tab2, tab3 = st.tabs(["Find Strategy", "Benchmark", "GA Configuration"])

with tab1:
    col_left, col_right = st.columns([1.5, 1])

    with col_right:
        st.write("📁 **Load Model**")
        uploaded_file = st.file_uploader("Drag CGS file here", type=["txt"])

        if uploaded_file:
            file = os.path.join(os.getcwd(), temp_path+'/temp_'+uploaded_file.name)
            if file != st.session_state['cgs_path']:
                st.session_state['result'] = None
                st.session_state['cgs_path'] = file
                with open(file, "wb") as f:
                    f.write(uploaded_file.getbuffer())

        st.subheader("NatATL Formula")
        formula = st.text_input("Write formula here:")
        if formula:
            st.session_state['formula_info'] = NatATL_formula_info(formula)
            file = os.path.join(os.getcwd(), temp_path+'/temp_formula.txt')
            st.session_state['formula_path'] = file
            with open(file, "w") as f:
                f.write(formula)

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

        st.write("---")

        if st.button("START ALGORITHM", use_container_width=True, type="primary"):
            if st.session_state['cgs_path'] and st.session_state['formula_path']:
                with st.spinner("Executing GA..."):
                    st.session_state['result'] = run_case(st.session_state['cgs_path'], st.session_state['formula_path'], vitamin=False, ga=True)['ga'][0]
                    st.rerun()

    with col_left:
        st.subheader("CGS graph visualization")
        graph_container = st.container(border=True)
        with graph_container:
            net = Network(height="600px", width="100%", directed=True, bgcolor="#ffffff")
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
            
            path = temp_path+'/temp_graph.html'
            net.save_graph(path)
            with open(path, 'r', encoding='utf-8') as f:
                import streamlit.components.v1 as components
                components.html(f.read(), height=600)

with tab2:
    st.subheader("Benchmarking Management")
    
    bench_col_left, bench_col_mid, bench_col_right = st.columns([1.2, 1, 1.2])
    
    with bench_col_left:
        @st.fragment(run_every=1.0) # Si auto-aggiorna ogni 1 secondo finché ci sono processi attivi
        def render_profiles_manager():
            
            st.markdown("### 📊 Benchmark Profiles")
            
            if st.button("➕ Add New Benchmark Profile", type="primary", use_container_width=True):
                st.session_state['show_add_form'] = True
                st.session_state['editing_profile_id'] = None
                st.rerun()

            st.write("")
            
            scrollable_container = st.container(height=500)
            with scrollable_container:
                if not st.session_state['benchmark_profiles']:
                    st.info("No benchmark profiles available. Click 'Add New Benchmark Profile' to create one.")
                else:
                    for profile in st.session_state['benchmark_profiles']:
                        p_id = profile['id']
                        
                        # Controlliamo se il processo per questo profilo è attualmente in vita
                        is_running = False
                        if p_id in st.session_state['running_processes']:
                            proc = st.session_state['running_processes'][p_id]
                            if proc.is_alive():
                                is_running = True
                            else:
                                # Il processo è terminato, lo rimuoviamo dalla memoria attiva
                                del st.session_state['running_processes'][p_id]

                        with st.container(border=True):
                            st.markdown(f"**{profile['name']}**")
                            if is_running:
                                st.markdown("🔴 **Status: Running...**")
                            else:
                                st.caption(f"{profile['description']}")
                            
                            col_run, col_edit, col_dl, col_del = st.columns([1, 1, 1, 1])
                            
                            with col_run:
                                if not is_running:
                                    if st.button("▶️ Run", key=f"run_{p_id}", use_container_width=True):
                                        settings_file = str(Path(temp_path) / f"profile_{p_id}" / "settings.json")
                                        def _target_run_benchmark(settings_path):
                                            run_benchmark(settings_path)
                                        
                                        # Avvio con multiprocessing
                                        p = multiprocessing.Process(target=_target_run_benchmark, args=(settings_file,))
                                        p.start()
                                        st.session_state['running_processes'][p_id] = p
                                        
                                        st.toast(f"Started benchmark: {profile['name']}")
                                        st.rerun()
                                else:
                                    if st.button("⏹️ Stop", key=f"stop_{p_id}", type="primary", use_container_width=True):
                                        try:
                                            parent = psutil.Process(proc.pid)
                                            children = parent.children(recursive=True)
                                            
                                            for child in children:
                                                child.terminate()
                                            
                                            parent.terminate()
                                            
                                            # Diamo un attimo per chiudersi pacificamente, altrimenti killiamo
                                            gone, alive = psutil.wait_procs(children + [parent], timeout=3)
                                            for p_alive in alive:
                                                p_alive.kill()
                                                
                                        except psutil.NoSuchProcess:
                                            pass
                                        except Exception as e:
                                            # Fallback sul metodo standard se psutil fallisce
                                            proc.terminate()
                                            proc.join()
                                        
                                        if p_id in st.session_state['running_processes']:
                                            del st.session_state['running_processes'][p_id]
                                        
                                        st.toast(f"Stopped benchmark: {profile['name']}")
                                        st.rerun()

                            with col_edit:
                                if not is_running:
                                    if st.button("✏️ Edit", key=f"edit_{p_id}", use_container_width=True):
                                        st.session_state['editing_profile_id'] = p_id
                                        st.session_state['show_add_form'] = False
                                        st.rerun()
                                else:
                                    st.button("✏️ Edit", key=f"edit_{p_id}", use_container_width=True, disabled=True)

                            with col_dl:
                                folder_path = Path(temp_path) / profile['folder_name']
                                if folder_path.exists():
                                    zip_data = zip_folder(folder_path)
                                    safe_filename = "".join(c for c in profile['name'] if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
                                    st.download_button(
                                        label="📥 Download",
                                        data=zip_data,
                                        file_name=f"{safe_filename}.zip",
                                        mime="application/zip",
                                        key=f"dl_{p_id}",
                                        use_container_width=True,
                                        help="Download profile folder"
                                    )

                            with col_del:
                                if not is_running:
                                    if st.button("🗑️", key=f"del_{p_id}", use_container_width=True, help="Delete profile"):
                                        folder_to_delete = Path(temp_path) / profile['folder_name']
                                        if folder_to_delete.exists():
                                            shutil.rmtree(folder_to_delete)
                                        st.session_state['benchmark_profiles'] = load_benchmark_profiles()
                                        st.success(f"Deleted profile '{profile['name']}'")
                                        st.rerun()
                                else:
                                    st.button("🗑️", key=f"del_{p_id}", use_container_width=True, disabled=True, help="Cannot delete while running")

            # Mostriamo quanti processi sono in esecuzione in tempo reale
            active_count = len(st.session_state['running_processes'])
            if active_count > 0:
                st.warning(f"⚠️ {active_count} benchmark process(es) currently running in background.")
            else:
                st.info("No active benchmark processes.")
        render_profiles_manager()

    with bench_col_mid:
        st.subheader("Plot Settings")
            
        if st.session_state['benchmark_profiles']:
            profile_options = {p['name']: p for p in st.session_state['benchmark_profiles']}
            selected_p_name = st.selectbox("Select Profile Results", list(profile_options.keys()), key="plot_profile_select")
            selected_profile = profile_options[selected_p_name]
            
            csv_output_path = selected_profile["data"].get("execution", {}).get("benchmark_output", "")
            directory = selected_profile["data"].get("execution", {}).get("directory", "")
            csv_fitness_path = str(Path(directory+"/output/generations.csv"))
            
            if csv_output_path and os.path.exists(csv_output_path):
                plot_type = st.selectbox("Plot Type", ["line", "distribution", "fitness"], key="plot_type_select")

                if plot_type != 'fitness':
                    keys_and_results = get_keys_and_results(csv_output_path)
                    selected = []
                    col1, col2 = st.columns([1, 1])
                    results1 = keys_and_results['results'][len(keys_and_results['results'])//2:]
                    results2 = keys_and_results['results'][:len(keys_and_results['results'])//2]
                    with col1:
                        for result in results1:
                            if st.checkbox(result):
                                selected.append(result)
                    with col2:
                        for result in results2:
                            if st.checkbox(result):
                                selected.append(result)

                if plot_type == 'line':
                    plot_key = st.selectbox("X-Axis Key", keys_and_results['keys'],key="plot_key_input")
                else: plot_key = None

                if st.button("📊 Generate Plot", use_container_width=True, type="primary"):
                    plot_temp_path = Path(directory + "/output/plot.png")
                    
                    try:
                        if plot_type != 'fitness':
                            draw_plot(
                                csv_file=csv_output_path,
                                plot_file=plot_temp_path,
                                plot_key=plot_key,
                                plot_type=plot_type,
                                results=selected
                            )
                        else:
                            draw_plot(
                                csv_file=csv_fitness_path,
                                plot_file=plot_temp_path,
                                plot_key=plot_key,
                                plot_type=plot_type,
                            )
                        st.session_state[f"last_plot_{selected_profile['id']}"] = plot_temp_path
                        st.success("Plot generated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating plot{csv_output_path}: {e}")
            else:
                st.warning(f"⚠️ Output CSV not found:\n`{csv_output_path}`")
        else:
            st.info("No profiles available.")

    # --- COLONNA DESTRA: VISUALIZZAZIONE IMMAGINE ---
    with bench_col_right:
        st.subheader("Plot Viewer")
        
        if st.session_state['benchmark_profiles']:
            # Ripeschiamo il profilo selezionato anche qui
            selected_p_name_right = st.session_state.get("plot_profile_select", None)
            if selected_p_name_right:
                selected_profile_right = profile_options.get(selected_p_name_right)
                if selected_profile_right:
                    plot_key_state = f"last_plot_{selected_profile_right['id']}"
                    
                    if plot_key_state in st.session_state and os.path.exists(st.session_state[plot_key_state]):
                        st.image(st.session_state[plot_key_state], caption=f"Plot ({selected_profile_right['name']})")
                        safe_filename = "".join(c for c in selected_profile_right['name'] if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
                        plot_path = temp_path+f"/profile_{selected_profile_right['id']}/output/plot.png"
                    
                        # Apertura del file immagine in modalità binaria per il download
                        with open(plot_path, "rb") as file:
                            btn = st.download_button(
                                label="📥 Download Plot (PNG)",
                                data=file,
                                file_name=f"{safe_filename}_plot.png",
                                mime="image/png",
                                key=f"download_plot_{selected_profile_right['id']}",
                                use_container_width=True
                            )
                    else:
                        st.info("Generate a plot from the middle column to see it here.")
        else:
            st.info("No plot to display.")
            
with tab3:
    st.subheader("GA configuration")
    settings_box = st.container(border=True)
    with settings_box:
        dyn_setts = st.checkbox("Automatic Settings", False)
        pop_size = st.number_input("Population Size", 1, 500, config.POPULATION_SIZE, disabled=dyn_setts)
        generations = st.number_input("Generations", 1, 1000, config.MAX_GENERATIONS, disabled=dyn_setts)
        elite = st.number_input("Elites", 0, 50, config.N_ELITE, disabled=dyn_setts)
        extra = st.number_input("Extras", 0, 50, config.EXTRA_STRATEGIES, disabled=dyn_setts)
        tournament = st.number_input("Tournament Size", 0, 50, config.TOURNAMENT_SIZE, disabled=dyn_setts)
        order_mut = st.slider("Order mutation Rate", 0.0, 1.0, config.ORDER_MUTATION)
        action_mut = st.slider("Action mutation Rate", 0.0, 1.0, config.ACTION_MUTATION)
        cond_mut = st.slider("Condition mutation Rate", 0.0, 1.0, config.CONDITION_MUTATION)
        dyn_k = st.number_input("Dynamic_k", 0, 10, config.DYNAMIC_K)
        if st.button("APPLY", use_container_width=True, type="primary"):
            config.set_config(pop_size, generations, elite, extra, tournament, order_mut, action_mut, cond_mut, dyn_k, dyn_setts)