"""
base_reader.py — Abstract base class cho mọi Reader (Tầng 11A-1).
"""
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd
from datetime import datetime


class BaseReader(ABC):
    """Base class cho CSV reader, Excel reader."""

    def __init__(self, source_id: str, source_config: dict):
        self.source_id = source_id
        self.config = source_config
        self.path = Path(source_config["path"])
        self.file_pattern = source_config["file_pattern"]
        self.encoding = source_config.get("encoding")
        self.delimiter = source_config.get("delimiter")
        self.sheet = source_config.get("sheet")

    def find_files(self) -> list:
        """Tìm tất cả file khớp pattern."""
        files = sorted(self.path.glob(self.file_pattern))
        if not files:
            raise FileNotFoundError(
                f"Không tìm thấy file khớp '{self.file_pattern}' trong {self.path}"
            )
        return files

    def _add_metadata(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        """Thêm metadata chuẩn: _raw_row_id, _source_file, _ingested_at."""
        df = df.copy()
        df["_raw_row_id"] = [f"{file_path.stem}_{i:06d}" for i in range(len(df))]
        df["_source_file"] = file_path.name
        df["_ingested_at"] = datetime.utcnow().isoformat() + "Z"
        return df

    @abstractmethod
    def read_file(self, file_path: Path) -> pd.DataFrame:
        """Đọc 1 file, trả về DataFrame."""
        pass

    def read_all(self) -> pd.DataFrame:
        """Đọc tất cả file khớp pattern, concat lại."""
        files = self.find_files()
        dfs = []
        for f in files:
            df = self.read_file(f)
            dfs.append(df)

        if len(dfs) == 1:
            return dfs[0]
        return pd.concat(dfs, ignore_index=True)
