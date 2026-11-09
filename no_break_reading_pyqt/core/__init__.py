"""Core modules for No Break Reading"""
from .eye_tracker import EyeTracker
from .alert_system import AlertSystem
from .pdf_reader import PDFReader
from .statistics_manager import StatisticsManager

__all__ = ['EyeTracker', 'AlertSystem', 'PDFReader', 'StatisticsManager']
