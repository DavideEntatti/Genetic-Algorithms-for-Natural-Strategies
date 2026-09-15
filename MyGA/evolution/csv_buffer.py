import csv
from pathlib import Path

class csv_buffer:
    buffer = []

    @classmethod
    def add_row(self, row):
        self.buffer.append(row)

    @classmethod
    def write_buffer(self, generations_path):
        csv_fields = ["Gen", "Fit", "Sol"]
        output_path = Path(generations_path)
        exists = False
        if output_path.exists():
            exists = True
        with output_path.open("a", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=csv_fields)
            if not exists:
                writer.writeheader()
            for row in self.buffer:
                writer.writerow(row)
            self.buffer.clear()
