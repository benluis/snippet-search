# process_data.py
import asyncio
from typing import List, Dict, Any
import textwrap
from get_data import search_pinecone


def process_query(query: str, top_k: int = 5) -> List[Dict[Any, Any]]:
    results = search_pinecone(query, top_k=top_k)
    return results.matches
