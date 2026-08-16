"""
Analyzers — Modulos de analise de codigo
"""

from .seguranca import SegurancaAnalyzer
from .compliance import ComplianceAnalyzer
from .leiturabilidade import LeiturabilidadeAnalyzer
from .navegabilidade import NavegabilidadeAnalyzer
from .ux_ui import UXUIAnalyzer
from .performance import PerformanceAnalyzer
from .operacional import OperacionalAnalyzer

__all__ = [
    "SegurancaAnalyzer",
    "ComplianceAnalyzer",
    "LeiturabilidadeAnalyzer",
    "NavegabilidadeAnalyzer",
    "UXUIAnalyzer",
    "PerformanceAnalyzer",
    "OperacionalAnalyzer",
]
