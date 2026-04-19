"""Cleanup script to rewrite search_service.py"""
content = """\"\"\"Legacy module - imports from new modular structure for backward compatibility.\"\"\"
from app.services.search import SearchService

__all__ = ["SearchService"]
"""

with open('app/services/search_service.py', 'w') as f:
    f.write(content)
print('search_service.py rewritten successfully')
