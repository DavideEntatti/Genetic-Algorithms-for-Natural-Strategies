from multiprocessing import Process, Queue
import time
from datetime import datetime
from MyGA.testing.running.vitamin_runner import run_vitamin
from MyGA.testing.running.ga_runner import run_ga
from MyGA.models.formula.fromula_functions import load_natatl_formulas

def vitamin_wrapper(formula, model_path, q):
    status, result = run_vitamin(formula, model_path)
    q.put((status, result))

def ga_wrapper(formula, model_path, q):
    status, result = run_ga(formula, model_path)
    q.put((status, result))

def run_case(model_path, formula_path, output_path=None, vitamin=True, ga=True, timeout=60):
    # Load formulas from the specified file
    formulas = load_natatl_formulas(formula_path)

    vitamin_runs = []
    ga_runs = []

    if output_path:
        with open(output_path, 'a') as f:
            f.write(f"# Run at {datetime.utcnow().isoformat()}Z\n")

    # Run each formula in a separate process
    for formula in formulas:
        if vitamin:
            q = Queue()
            p = Process(target=vitamin_wrapper, args=(formula, model_path, q))
            t1 = time.perf_counter()
            p.start()
            p.join(timeout=timeout)
            if p.is_alive():
                p.terminate()  # Forza la chiusura
                p.join()
                vitamin_status, vitamin_result = 'Timeout', None
            else:
                vitamin_status, vitamin_result = q.get()
            t2 = time.perf_counter()
            vitamin_time = t2 - t1
        else:
            vitamin_status, vitamin_result, vitamin_time = 'Skipped', None, 0.0

        vitamin_runs.append((vitamin_status, vitamin_result, vitamin_time))

        if ga:
            q = Queue()
            p = Process(target=ga_wrapper, args=(formula, model_path, q))
            t1 = time.perf_counter()
            p.start()
            p.join(timeout=timeout)
            if p.is_alive():
                p.terminate()  # Forza la chiusura
                p.join()
                ga_status, ga_result = 'Timeout', None
            else:
                ga_status, ga_result = q.get()
            t2 = time.perf_counter()
            ga_time = t2 - t1
        else:
            ga_status, ga_result, ga_time = 'Skipped', None, 0.0

        ga_runs.append((ga_status, ga_result, ga_time))

        if vitamin_status == True and ga_status != "Found":
            print(vitamin_result)
            raise Exception(f"Vitamin found a solution but GA did not for formula: {formula}")

        # Print the results for the current formula
        if output_path:
            with open(output_path, 'a') as f:
                f.write(f"Formula: {formula}\n")
                f.write(f"Vitamin Status: {vitamin_status}, Result: {vitamin_result}, Time: {vitamin_time:.4f} seconds\n")
                if ga_status == 'Found':
                    f.write(f"GA Status: {ga_status}, Result: {ga_result.get_strategy()}, Time: {ga_time:.4f} seconds\n")
                else:
                    f.write(f"GA Status: {ga_status}, Result: {ga_result}, Time: {ga_time:.4f} seconds\n")
                f.write("\n")
        # else:
        #     print(f"Formula: {formula}")
        #     print(f"Vitamin Status: {vitamin_status}, Result: {vitamin_result}, Time: {vitamin_time:.4f} seconds")
        #     print(f"GA Status: {ga_status}, Result: {ga_result}, Time: {ga_time:.4f} seconds")

    return {'ga': ga_runs, 'vitamin': vitamin_runs}

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--vitamin', action='store_true')
    p.add_argument('--ga', action='store_true')
    p.add_argument('--timeout', type=int, default=60, help='Timeout for each process in seconds')
    p.add_argument('--module-file', type=str, help='Optional path to a file where the generated CGS will be saved')
    p.add_argument('--formula-file', type=str, help='Path to a file with one NatATL formula per line')
    p.add_argument('--output-file', type=str, help='Path to the output file for timing results')
    args = p.parse_args()

    run_case(model_path=args.module_file, formula_path=args.formula_file, output_path=args.output_file, vitamin=args.vitamin, ga=args.ga, timeout=args.timeout)