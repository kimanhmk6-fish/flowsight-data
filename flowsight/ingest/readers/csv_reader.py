"""
csv_reader.py — Đọc CSV với encoding/delimiter linh hoạt.
"""
import pandas as pd
from pathlib import Path
from .base_reader import BaseReader


class CSVReader(BaseReader):
    """Đọc CSV, xử lý BOM/no-BOM, delimiter khác nhau."""

    def read_file(self, file_path: Path) -> pd.DataFrame:
        try:
            df = pd.read_csv(
                file_path,
                encoding=self.encoding or "utf-8",
                sep=self.delimiter or ",",
                dtype=str,
                keep_default_na=False,
                na_values=[""],
            )
        except UnicodeDecodeError:
            # Fallback: thử utf-8-sig
            df = pd.read_csv(
                file_path,
                encoding="utf-8-sig",
                sep=self.delimiter or ",",
                dtype=str,
                keep_default_na=False,
                na_values=[""],
            )

        return self._add_metadata(df, file_path)
