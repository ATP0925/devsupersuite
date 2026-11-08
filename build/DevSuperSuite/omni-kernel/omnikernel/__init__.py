"""
OmniKernel 5.0: Autonomous VibeCoding OS & Neural Context Compressor for Cursor & Claude Code.
"""

__version__ = "5.0.0"
__author__ = "DevSuperSuite Labs"

from .compressor import ASTContextCompressor, estimate_token_count
from .invariants import InvariantGuard

__all__ = ["ASTContextCompressor", "estimate_token_count", "InvariantGuard"]

