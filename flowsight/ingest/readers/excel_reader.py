"""
excel_reader.py — Đọc Excel multi-sheet (cho SRC-05 QC Sampling, SRC-09 Incident).
"""
import pandas as pd
from pathlib import Path
from .base_reader import BaseReader


class ExcelReader(BaseReader):
    """Đọc Excel, concat nhiều sheet, giữ cột _source_sheet."""

    def read_file(self, file_path: Path) -> pd.DataFrame:
        xl = pd.ExcelFile(file_path)
        dfs = []

        for sheet_name in xl.sheet_names:
            df = xl.parse(
                sheet_name,
                dtype=str,
                keep_default_na=False,
                na_values=[""],
            )
            df["_source_sheet"] = sheet_name
            dfs.append(df)

        df_all = pd.concat(dfs, ignore_index=True)
        return self._add_metadata(df_all, file_path)
