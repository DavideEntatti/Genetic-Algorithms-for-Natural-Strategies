from multiprocessing import Process, Queue
import time
import psutil
from datetime import datetime
from MyGA.testing.running.vitamin_runner import run_vitamin
from MyGA.testing.running.ga_runner import run_ga
from MyGA.models.formula.fromula_functions import load_natatl_formulas

def vitamin_wrapper(formula, model_path, q):
    status, result = run_vitamin(formula, model_path)
    q.put((status, result))

def ga_wrapper(formula, model_path, q, csv_buffer=None):
    status, result = run_ga(formula, model_path, csv_buffer)
    q.put((status, result))

def run_case(model_path, formula_path, output_path=None, csv_buffer=None, vitamin=True, ga=True, mixed=True, timeout=60):
    # Load formulas from the specified file
    formulas = load_natatl_formulas(formula_path)

    vitamin_runs = []
    ga_runs = []
    mixed_runs = []

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
                # Uccisione profonda con psutil
                try:
                    parent = psutil.Process(p.pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass
                p.join()
                vitamin_status, vitamin_result = False, None
                print("vitamin timeout")
            else:
                vitamin_status, vitamin_result = q.get()
            t2 = time.perf_counter()
            vitamin_time = t2 - t1
        else:
            vitamin_status, vitamin_result, vitamin_time = 'Skipped', None, timeout

        vitamin_runs.append((vitamin_status, vitamin_result, vitamin_time))

        if not csv_buffer:
            if ga:
                q = Queue()
                p = Process(target=ga_wrapper, args=(formula, model_path, q, csv_buffer))
                t1 = time.perf_counter()
                p.start()
                p.join(timeout=timeout)
                if p.is_alive():
                    # Uccisione profonda con psutil
                    try:
                        parent = psutil.Process(p.pid)
                        for child in parent.children(recursive=True):
                            child.kill()
                        parent.kill()
                    except psutil.NoSuchProcess:
                        pass
                    p.join()
                    ga_status, ga_result = 'Timeout', None
                else:
                    ga_status, ga_result = q.get()
                t2 = time.perf_counter()
                ga_time = t2 - t1
            else:
                ga_status, ga_result, ga_time = 'Skipped', None, 0.0

        else:
            if ga:
                t1 = time.perf_counter()
                ga_status, ga_result = run_ga(formula, model_path, csv_buffer)
                t2 = time.perf_counter()
                ga_time = t2 - t1
                csv_buffer.write_buffer()
            else:
                ga_status, ga_result, ga_time = 'Skipped', None, 0.0

        ga_runs.append((ga_status, ga_result, ga_time))

        if mixed:
            if ga_status == 'Found':
                mixed_time = ga_time
                mixed_result = 'ga'
                mixed_status = True
            elif ga_status == 'No solution':
                mixed_time = ga_time
                mixed_result = None
                mixed_status = False
            elif vitamin_status:
                mixed_status = True
                mixed_time = ga_time + vitamin_time
                mixed_result = 'vitamin'
            else:
                mixed_status = False
                mixed_time = ga_time + vitamin_time
                mixed_result = None
        else:
            mixed_status, mixed_result, mixed_time = 'Skipped', None, 0.0

        mixed_runs.append((mixed_status, mixed_result, mixed_time))

        # Print the results for the current formula
        if output_path:
            with open(output_path, 'a') as f:
                f.write(f"Formula: {formula}\n")
                f.write(f"Vitamin Status: {vitamin_status}, Result: {vitamin_result}, Time: {vitamin_time:.4f} seconds\n")
                f.write(f"Mixed Status: {mixed_status}, Result: {mixed_result}, Time: {mixed_time:.4f} seconds\n")
                if ga_status == 'Found':
                    f.write(f"GA Status: {ga_status}, Result: {ga_result.get_strategy()}, Time: {ga_time:.4f} seconds\n")
                else:
                    f.write(f"GA Status: {ga_status}, Result: {ga_result}, Time: {ga_time:.4f} seconds\n")
                f.write("\n")

        #if vitamin_status == True and ga_status != "Found":
            #print(vitamin_result)
            #print(f"Vitamin found a solution but GA did not for formula: {formula}")
            #raise Exception(f"Vitamin found a solution but GA did not for formula: {formula}")
        
        #if vitamin_status == False and ga_status == "Found":
            #print(ga_result.get_strategy())
            #print(f"GA found a solution but Vitamin did not for formula: {formula}")
            #raise Exception(f"GA found a solution but Vitamin did not for formula: {formula}")
            
        # else:
        #     print(f"Formula: {formula}")
        #     print(f"Vitamin Status: {vitamin_status}, Result: {vitamin_result}, Time: {vitamin_time:.4f} seconds")
        #     print(f"GA Status: {ga_status}, Result: {ga_result}, Time: {ga_time:.4f} seconds")

    return {'ga': ga_runs, 'vitamin': vitamin_runs, 'mixed': mixed_runs}

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--vitamin', action='store_true')
    p.add_argument('--ga', action='store_true')
    p.add_argument('--mixed', action='store_true')
    p.add_argument('--timeout', type=int, default=60, help='Timeout for each process in seconds')
    p.add_argument('--module-file', type=str, help='Optional path to a file where the generated CGS will be saved')
    p.add_argument('--formula-file', type=str, help='Path to a file with one NatATL formula per line')
    p.add_argument('--output-file', type=str, help='Path to the output file for timing results')
    args = p.parse_args()

    run_case(model_path=args.module_file, formula_path=args.formula_file, output_path=args.output_file, vitamin=args.vitamin, ga=args.ga, mixed=args.mixed, timeout=args.timeout)