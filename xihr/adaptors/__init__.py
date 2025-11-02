"""Data adaptor implementations for xihr."""

from .base import DataAdaptor
from .csv_adaptor import CSVDataAdaptor
from .db_adaptor import DBDataAdaptor
from .excel_adaptor import ExcelDataAdaptor

__all__ = [
    "DataAdaptor",
    "CSVDataAdaptor",
    "DBDataAdaptor",
    "ExcelDataAdaptor",
]
"""Public adaptor exports."""
