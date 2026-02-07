"""
University Comparison module.

Provides server-side filtering and comparison for the university comparison page.
Replaces the client-side approach of loading ALL programs/prices/preferences
with targeted queries that return only what the frontend needs.
"""

from app.modules.university_comparison.router import router as university_comparison_router

__all__ = ["university_comparison_router"]
