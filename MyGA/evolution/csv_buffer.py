import csv
from pathlib import Path

class CSV_buffer:

    def __init__(self, csv_path):
        self.path = Path(csv_path)
        self.buffer = []
        if self.path.exists():
            exists = True
            import os
            os.remove(self.path)

    def add_row(self, row):
        self.buffer.append(row)

    def write_buffer(self):
        csv_fields = ["Gen", "Fit", "Sol"]
        exists = False
        if self.path.exists():
            exists = True
        with self.path.open("a", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=csv_fields)
            if not exists:
                writer.writeheader()
            for row in self.buffer:
                writer.writerow(row)
            self.buffer.clear()
