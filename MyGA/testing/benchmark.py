from MyGA.testing.running.case_runner import run_case
from MyGA.testing.generation.case_generator import generate_case
import csv
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

def run_benchmark(settings_path):
    with open(settings_path, 'r') as f:
        settings = json.load(f)

        start = settings['start_parameters']
        final = settings['execution_plan']['final_values']
        num_configs = settings['execution_plan']['num_configs']
        iterations = settings['execution_plan']['iterations_per_config']
        templates = settings['template_parameters']['templates'] * int(settings['template_parameters']['template_repetitions'])

        vitamin = False
        ga = False
        mixed = False
        if settings['execution']['vitamin'] == 1:
            vitamin = True
        if settings['execution']['ga'] == 1:
            ga = True
        if vitamin and ga and settings['execution']['mixed'] == 1:
            mixed = True
        timeout = settings['execution']['timeout']
        benchmark_output_path = settings['execution']['benchmark_output']
        output_dir = settings['execution']['directory']
        #output_dir.mkdir(parents=True, exist_ok=True)

        output_path = Path(benchmark_output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        enabled_algorithms = [
            algorithm
            for algorithm, enabled in (("vitamin", vitamin), ("ga", ga), ("mixed", mixed))
            if enabled
        ]
        csv_fields = ["configuration"] + list(start.keys())
        for algorithm in enabled_algorithms:
            csv_fields.extend([
                f"{algorithm}_wins",
                f"{algorithm}_losses",
                f"{algorithm}_winning_time_avg",
                f"{algorithm}_losing_time_avg",
            ])

        with output_path.open("w", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=csv_fields)
            writer.writeheader()
            current_config = 0

            while(current_config < num_configs):
                print("new config")
                algorithm_runs = {algorithm: [] for algorithm in enabled_algorithms}
                current_iter = 0
                #config_dir = Path(str(output_dir)+f'\config{current_config}')
                #config_dir.mkdir(parents=True, exist_ok=True)
                progress = current_config/(num_configs-1) if num_configs > 1 else 0
                step = {}
                for key in start:
                    if isinstance(start[key], (int, float)) and f"fin_{key}" in final:
                        step[key] = start[key]+(final[f"fin_{key}"] - start[key])*progress
                        if isinstance(start[key], int):
                            step[key] = int(step[key])
                    else:
                        step[key] = start[key]
                while(current_iter < iterations):
                    for key in start:
                        if isinstance(start[key], list):
                            if isinstance(start[key][0], float) or isinstance(start[key][1], float):
                                step[key] = random.uniform(start[key][0], start[key][1])
                            else:
                                step[key] = random.randint(start[key][0], start[key][1])
                    # case_dir = Path(str(output_dir)+f'\case{current_iter+1}')
                    # case_dir.mkdir(parents=True, exist_ok=True)
                    model_path = str(output_dir)+f'/cgs.txt'
                    formula_path = str(output_dir)+f'/formulas.txt'
                    #out_path = str(output_dir)+f'/out.txt'
                    generate_case(
                        num_states=step['num_states'],
                        num_agents=step['num_agents'],
                        num_aps=step['num_aps'],
                        num_agent_actions=step['num_agent_actions'],
                        sparsity=step['sparsity'],
                        coalition_size=step['coalition_size'],
                        k=step['k'],
                        formula_length=step['set_size'],
                        templates=templates,
                        cgs_file=model_path,
                        formula_file=formula_path
                    )
                    runs = run_case(model_path, formula_path, vitamin=vitamin, ga=ga, mixed=mixed, timeout=timeout)
                    if vitamin:
                        algorithm_runs["vitamin"].extend(runs["vitamin"])
                    if ga:
                        algorithm_runs["ga"].extend(runs["ga"])
                    if mixed:
                        algorithm_runs["mixed"].extend(runs["mixed"])
                    
                    current_iter +=1

                row = {"configuration": current_config + 1, **step}
                for algorithm, runs_for_algorithm in algorithm_runs.items():
                    is_win = lambda run: (
                        run[0] is True if algorithm == "vitamin" or algorithm == "mixed" else run[0] == "Found"
                    )
                    winning_times = [run[2] for run in runs_for_algorithm if is_win(run)]
                    losing_times = [run[2] for run in runs_for_algorithm if not is_win(run)]
                    row[f"{algorithm}_wins"] = len(winning_times)
                    row[f"{algorithm}_losses"] = len(losing_times)
                    row[f"{algorithm}_winning_time_avg"] = (
                        sum(winning_times) / len(winning_times) if winning_times else 0
                    )
                    row[f"{algorithm}_losing_time_avg"] = (
                        sum(losing_times) / len(losing_times) if losing_times else 0
                    )
                writer.writerow(row)

                current_config +=1

    

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--settings', default=str(HERE / 'default_settings.json'), help='Path to settings file')
    args = p.parse_args()
    run_benchmark(args.settings)