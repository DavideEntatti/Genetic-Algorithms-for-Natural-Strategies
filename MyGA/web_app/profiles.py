import streamlit as st
import json
from pathlib import Path
import shutil
import io
import zipfile

temp_path = "MyGA/web_app/temp"
folder = Path(temp_path)
folder.mkdir(parents=True, exist_ok=True)

def load_benchmark_profiles():
    profiles = []
    if folder.exists():
        for item in folder.iterdir():
            if item.is_dir() and item.name.startswith("profile_"):
                json_file = item / "settings.json"
                if json_file.exists():
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            p_id = int(item.name.split("_")[1])
                            
                            meta = data.get("benchmark_metadata", {})
                            exec_data = data.get("execution", {})
                            
                            profiles.append({
                                "id": p_id,
                                "name": meta.get("name", f"Profile {p_id}"),
                                "description": meta.get("description", ""),
                                "timeout": exec_data.get("timeout", 120),
                                "folder_name": item.name,
                                "data": data
                            })
                    except Exception as e:
                        print(f"Error loading {json_file}: {e}")
    profiles.sort(key=lambda x: x["id"])
    return profiles

def save_profile_to_disk(profile_id, profile_data):
    profile_folder = Path(temp_path) / f"profile_{profile_id}"
    profile_folder.mkdir(parents=True, exist_ok=True)
    json_file = profile_folder / "settings.json"
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=4)

def render_profile_form(form_key, data=None):
    if data is None:
        current_profiles = st.session_state.get('benchmark_profiles', [])
        new_id = max([p["id"] for p in current_profiles], default=0) + 1
        profile_folder = Path(temp_path) / f"profile_{new_id}"
        
        data = {
            "benchmark_metadata": {"name": "New Benchmark", "description": "Description here"},
            "execution": {
                "ga": 1, "vitamin": 1, "mixed": 1, "timeout": 120, 
                "directory": str(profile_folder),
                "benchmark_output": str(profile_folder / "output" / "benchmark_output.csv")
            },
            "start_parameters": {"num_states": 4, "num_agents": 2, "num_agent_actions": 2, "num_aps": 3, "sparsity": 0.5, "coalition_size": 1, "k": 1, "set_size": 3},
            "execution_plan": {
                "iterations_per_config": 5, "num_configs": 6,
                "final_values": {"fin_num_states": 9, "fin_num_agents": 4, "fin_num_agent_actions": 4, "fin_num_aps": 6, "fin_sparsity": 0.5, "fin_coalition_size": 2, "fin_k": 1, "fin_set_size": 3}
            },
            "template_parameters": {"templates": ["G", "F", "X", "U"], "template_repetitions": 6}
        }
    
    # Ricaviamo sempre la cartella come oggetto Path o stringa sicura
    exec_dir = data["execution"].get("directory", "")
    profile_folder = Path(exec_dir) if exec_dir else Path(temp_path) / "profile_temp"

    meta = data.get("benchmark_metadata", {})
    exec_data = data.get("execution", {})
    start_p = data.get("start_parameters", {})
    plan = data.get("execution_plan", {})
    fin_v = plan.get("final_values", {})
    tpl = data.get("template_parameters", {})

    with st.form(form_key):
        p_name = st.text_input("Profile Name", value=meta.get("name", ""))
        p_desc = st.text_area("Description", value=meta.get("description", ""))
        
        st.divider()
        st.markdown("#### Execution Settings")
        col1, col2, col3 = st.columns(3)
        with col1:
            ga = st.checkbox("GA Enabled", value=bool(exec_data.get("ga", 1)))
            vitamin = st.checkbox("Vitamin Enabled", value=bool(exec_data.get("vitamin", 1)))
        with col2:
            mixed = st.checkbox("Mixed Enabled", value=bool(exec_data.get("mixed", 1)))
            timeout = st.number_input("Timeout (s)", value=exec_data.get("timeout", 120))
        with col3:
            gen_out = "generations_output" in exec_data 
            if st.checkbox("Save generations", value=bool(gen_out)):
                generations_output = str(profile_folder / "output" / "generations.csv")
            else:
                generations_output = None
            cases_out = "cases_output" in exec_data 
            if st.checkbox("Save cases", value=bool(cases_out)):
                cases_output = str(profile_folder / "output" / "cases.txt")
            else:
                cases_output = None

        st.divider()
        st.markdown("#### Parameters Configuration")

        def param_row(label, key_name, default_start, default_final, is_float=False):
            st.markdown(f"**{label}**")
            
            is_list_val = isinstance(default_start, list)
            current_mode = "Randomize" if is_list_val else "Scale"
            
            if is_list_val:
                val1 = default_start[0]
                val2 = default_start[1]
            else:
                val1 = default_start
                val2 = default_final

            col_mode, c1, c_to, c2 = st.columns([3, 7, 1, 7])
            
            with col_mode:
                mode = st.selectbox("Mode", ["Scale", "Randomize"], index=0 if current_mode=="Scale" else 1, key=f"mode_{key_name}", label_visibility="collapsed")
            
            with c1:
                v1 = st.number_input(f"Val 1 {label}", value=val1, format="%.2f" if is_float else "%d", label_visibility="collapsed")
            
            if mode == "Scale":
                with c_to:
                    st.markdown("<p style='text-align: center; margin-top: 8px;'>to</p>", unsafe_allow_html=True)
                with c2:
                    v2_input = st.text_input(f"Val 2 {label}", value=str(val2) if val2 is not None else "", label_visibility="collapsed", placeholder="Same as initial")
                try:
                    if v2_input.strip() == "":
                        v2 = v1
                    else:
                        v2 = float(v2_input) if is_float else int(v2_input)
                except ValueError:
                    v2 = v1
                return (v1, v2), "scale"
            else:
                with c_to:
                    st.markdown("<p style='text-align: center; margin-top: 8px;'>and</p>", unsafe_allow_html=True)
                with c2:
                    v_max = st.number_input(f"Val Max {label}", value=val2 if val2 >= val1 else val1, format="%.2f" if is_float else "%d", label_visibility="collapsed")
                return [v1, v_max], "randomize"

        ns_res, ns_mode = param_row("Num States", "num_states", start_p.get("num_states", 4), fin_v.get("fin_num_states", 9))
        na_res, na_mode = param_row("Num Agents", "num_agents", start_p.get("num_agents", 2), fin_v.get("fin_num_agents", 4))
        naa_res, naa_mode = param_row("Num Agent Actions", "num_agent_actions", start_p.get("num_agent_actions", 2), fin_v.get("fin_num_agent_actions", 4))
        nap_res, nap_mode = param_row("Num APs", "num_aps", start_p.get("num_aps", 3), fin_v.get("fin_num_aps", 6))
        sp_res, sp_mode = param_row("Sparsity", "sparsity", start_p.get("sparsity", 0.5), fin_v.get("fin_sparsity", 0.5), is_float=True)
        cs_res, cs_mode = param_row("Coalition Size", "coalition_size", start_p.get("coalition_size", 1), fin_v.get("fin_coalition_size", 2))
        k_res, k_mode = param_row("K", "k", start_p.get("k", 1), fin_v.get("fin_k", 1))
        ss_res, ss_mode = param_row("Set Size", "set_size", start_p.get("set_size", 3), fin_v.get("fin_set_size", 3))

        st.divider()
        st.markdown("#### Execution Plan & Templates")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            iterations_per_config = st.number_input("Iterations per Config", value=plan.get("iterations_per_config", 5), min_value=1)
            num_configs = st.number_input("Num Configs", value=plan.get("num_configs", 6), min_value=1)
        with col_p2:
            templates_str = st.text_input("Templates (comma separated)", value=", ".join(tpl.get("templates", ["G", "F", "X", "U"])))
            template_repetitions = st.number_input("Template Repetitions", value=tpl.get("template_repetitions", 6), min_value=1)

        st.write("")
        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("Save Profile", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        start_parameters = {}
        final_values = {}

        params_data = [
            ("num_states", ns_res, ns_mode),
            ("num_agents", na_res, na_mode),
            ("num_agent_actions", naa_res, naa_mode),
            ("num_aps", nap_res, nap_mode),
            ("sparsity", sp_res, sp_mode),
            ("coalition_size", cs_res, cs_mode),
            ("k", k_res, k_mode),
            ("set_size", ss_res, ss_mode)
        ]

        for p_key, p_val, p_m in params_data:
            if p_m == "scale":
                start_parameters[p_key] = p_val[0]
                final_values[f"fin_{p_key}"] = p_val[1]
            else:
                start_parameters[p_key] = p_val
                final_values[f"fin_{p_key}"] = p_val[1]

        dir_str = str(profile_folder)

        execution = {
            "ga": int(ga), 
            "vitamin": int(vitamin), 
            "mixed": int(mixed), 
            "timeout": int(timeout), 
            "directory": dir_str,
            "benchmark_output": str(Path(dir_str) / "output" / "benchmark_output.csv")
        }
        
        if generations_output: 
            execution["generations_output"] = str(Path(dir_str) / "output" / "generations.csv")
        if cases_output: 
            execution["cases_output"] = str(Path(dir_str) / "output" / "cases.txt")
        return {
            "submitted": submitted,
            "cancelled": cancelled,
            "p_name": p_name,
            "data": {
                "benchmark_metadata": {"name": p_name, "description": p_desc},
                "execution": execution,
                "start_parameters": start_parameters,
                "execution_plan": {
                    "iterations_per_config": int(iterations_per_config),
                    "num_configs": int(num_configs),
                    "final_values": final_values
                },
                "template_parameters": {"templates": [t.strip() for t in templates_str.split(",")], "template_repetitions": int(template_repetitions)}
            }
        }

def zip_folder(folder_path):
    folder_path = Path(folder_path)  # Converte in Path se è una stringa
    bytes_io = io.BytesIO()
    with zipfile.ZipFile(bytes_io, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in folder_path.rglob('*'):
            if file_path.is_file():
                zip_file.write(file_path, file_path.relative_to(folder_path.parent))
    bytes_io.seek(0)
    return bytes_io

@st.dialog("Add New Benchmark Profile", width="large")
def add_profile_dialog():
    result = render_profile_form("add_profile_form")
    if result["submitted"]:
        if result["p_name"]:
            current_profiles = st.session_state.get('benchmark_profiles', [])
            new_id = max([p["id"] for p in current_profiles], default=0) + 1
            save_profile_to_disk(new_id, result["data"])
            st.session_state['benchmark_profiles'] = load_benchmark_profiles()
            st.success("Profile added successfully!")
            st.rerun()
        else:
            st.error("Please enter a profile name.")
    if result["cancelled"]:
        st.rerun()

@st.dialog("Edit Benchmark Profile", width="large")
def edit_profile_dialog(profile_id):
    profile_item = next((p for p in st.session_state.get('benchmark_profiles', []) if p["id"] == profile_id), None)
    if profile_item:
        result = render_profile_form(f"edit_profile_form_{profile_id}", data=profile_item["data"])
        if result["submitted"]:
            if result["p_name"]:
                save_profile_to_disk(profile_id, result["data"])
                st.session_state['benchmark_profiles'] = load_benchmark_profiles()
                st.success("Profile updated successfully!")
                st.rerun()
            else:
                st.error("Please enter a profile name.")
        if result["cancelled"]:
            st.rerun()