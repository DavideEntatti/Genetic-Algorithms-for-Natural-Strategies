import csv

def _available_keys(rows):
    results = _available_results(rows)
    if not rows:
        return []
    keys = []
    for column in rows[0]:
        if not column in results:
            keys.append(column)
    return keys

def _available_results(rows):
    """Return result columns that exist and contain at least one numeric value."""
    if not rows:
        return []
    result_columns = []
    for column in rows[0]:
        if column in {"configuration"} or not (
            column.endswith("_wins")
            or column.endswith("_losses")
            or column.endswith("_winning_time_avg")
            or column.endswith("_losing_time_avg")
        ):
            continue
        if any(row.get(column, "").strip() for row in rows):
            result_columns.append(column)
    return result_columns


def _selected_results(rows, results):
    available = _available_results(rows)
    if results is None:
        return available
    unknown = [result for result in results if result not in available]
    if unknown:
        raise ValueError(f"Unknown or empty result columns: {', '.join(unknown)}")
    return results


def draw_plot(
    csv_file,
    plot_file,
    plot_key="configuration",
    plot_type="line",
    results=None,
):
    import matplotlib.pyplot as plt

    with open(csv_file, newline="") as source:
        rows = list(csv.DictReader(source))

    if not rows:
        raise ValueError(F"The benchmark CSV does not contain any configurations {csv_file}")
    if plot_key not in rows[0] and plot_type != "fitness":
        raise ValueError(f"Unknown plot key:{plot_key}")

    if plot_type != 'fitness':
        selected = _selected_results(rows, results)
        if not selected:
            raise ValueError("The CSV does not contain any selected result")

    if plot_type not in {"line", "distribution", "fitness"}:
        raise ValueError("Invalid plot_type")

    if plot_type == "line":
        _draw_line_plot(rows, selected, plot_file, plot_key, results,)
    elif plot_type == "distribution":
        _draw_distribution(rows, selected, plot_file)
    elif plot_type == "fitness":
        _draw_fitness_plot(csv_file, plot_file)
    return

def _draw_line_plot(
    rows,
    selected,
    plot_file,
    plot_key="configuration",
    results=None,
):
    import matplotlib.pyplot as plt

    x_values = [float(row[plot_key]) for row in rows]
    fig, ax1 = plt.subplots()

    time_results = [result for result in selected if "time_avg" in result]
    count_results = [result for result in selected if "time_avg" not in result]
    for index, field in enumerate(time_results):
        ax1.plot(
            x_values,
            [float(row[field]) for row in rows],
            label=field,
            marker="o",
            linestyle="-" if "winning" in field else "--",
        )

    ax1.set_ylabel('Tempo (secondi)', fontweight='bold')
    ax1.set_xlabel(plot_key, fontweight='bold')

    ax1.ticklabel_format(useOffset=False, style='plain', axis='y')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Cases')

    for index, field in enumerate(count_results):
        ax2.plot(
            x_values,
            [float(row[field]) for row in rows],
            label=field,
            marker="s" if "wins" in field else "x",
            linestyle=":",
        )

    ax2.ticklabel_format(useOffset=False, style='plain', axis='y')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    plt.legend(lines1 + lines2, labels1 + labels2, loc='best', frameon=True)

    plt.title('Benchmark execution times and outcomes')
    ax1.grid(True, linestyle=':', alpha=0.6)
    fig.savefig(plot_file)


def _draw_distribution(rows, selected, plot_file):
    import matplotlib.pyplot as plt
    import statistics

    fig, ax = plt.subplots()
    for field in selected:
        values = [float(row[field]) for row in rows if row.get(field, "").strip()]
        if values:
            ax.hist(values, bins="auto", alpha=0.55, label=field)
            if len(values) > 1:
                var_value = statistics.variance(values)  # Varianza campionaria (N-1)
                print(f"Varianza per '{field}': {var_value:.4f}")
            else:
                print(f"Varianza per '{field}': Dati insufficienti (1 solo valore)")

    ax.set_xlabel("Valore del risultato")
    ax.set_ylabel("Frequenza")
    ax.set_title("Distribuzione dei risultati")
    ax.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(plot_file)

def _draw_fitness_plot(csv_file, plot_file):
    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.read_csv(csv_file)
    
    df['Sol'] = df['Sol'].astype(int)
    
    grouped = df.groupby('Gen').agg({
        'Fit': 'mean',
        'Sol': 'sum'
    }).reset_index()
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    
    color = 'tab:blue'
    ax1.set_xlabel('Gen (Generazione)')
    ax1.set_ylabel('Media Fitness', color=color)
    line1 = ax1.plot(grouped['Gen'], grouped['Fit'], color=color, marker='o', label='Media Fit')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    ax2 = ax1.twinx()  
    color = 'tab:orange'
    ax2.set_ylabel('Soluzioni trovate', color=color)
    line2 = ax2.plot(grouped['Gen'], grouped['Sol'], color=color, marker='s', linestyle='--', label='Somma Sol')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title("Andamento Media Fit e Somma Sol per Generazione")
    fig.tight_layout()

    fig.savefig(plot_file)

def get_keys_and_results(csv_file):
    with open(csv_file, newline="") as source:
        rows = list(csv.DictReader(source))
    
    return {"keys": _available_keys(rows), "results": _available_results(rows)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plot a benchmark CSV")
    parser.add_argument("csv_file")
    parser.add_argument("plot_file")
    parser.add_argument("--plot-key", default="configuration")
    parser.add_argument("--plot-type", choices=("line", "distribution", "fitness"), default="line")
    parser.add_argument(
        "--results",
        help="Comma-separated CSV result columns; defaults to all available columns",
    )
    args = parser.parse_args()
    selected_results = args.results.split(",") if args.results else None
    draw_plot(
        args.csv_file,
        args.plot_file,
        args.plot_key,
        args.plot_type,
        selected_results,
    )