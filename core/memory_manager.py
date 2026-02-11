"""
Memory Manager - Gestion de la mémoire conversationnelle par user_id

Stockage historique et nettoyage automatique des sessions inactives
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# Stockage global mémoire (user_id -> {history, last_active})
conversation_memory: Dict[str, Dict[str, Any]] = {}


def build_chat_history(history_pairs: List[Dict[str, str]]) -> str:
    """
    Construit l'historique conversationnel formaté
    
    Args:
        history_pairs: Liste de dicts {"A": user_msg, "B": assistant_msg}
        
    Returns:
        String formaté pour le prompt
    """
    if not history_pairs:
        return ""
    
    lines = []
    for pair in history_pairs:
        user_msg = pair.get("A", "")
        assistant_msg = pair.get("B", "")
        
        if user_msg:
            lines.append(f"User: {user_msg}")
        if assistant_msg:
            lines.append(f"Assistant: {assistant_msg}")
    
    return "\n".join(lines)


async def cleanup_task(
    inactivity_timeout: timedelta,
    check_interval: int
):
    """
    Tâche asynchrone de nettoyage des sessions inactives
    
    Args:
        inactivity_timeout: Durée d'inactivité avant suppression
        check_interval: Intervalle vérification (secondes)
    """
    logger.info(f"🧹 Cleanup task started (timeout={inactivity_timeout}, interval={check_interval}s)")
    
    while True:
        await asyncio.sleep(check_interval)
        
        now = datetime.utcnow()
        to_delete = []
        
        for user_id, session in conversation_memory.items():
            last_active = session.get("last_active")
            
            if last_active and (now - last_active) > inactivity_timeout:
                to_delete.append(user_id)
        
        # Supprimer sessions expirées
        for user_id in to_delete:
            del conversation_memory[user_id]
            logger.info(f"🗑️  Cleaned up session: {user_id}")
        
        if to_delete:
            logger.info(f"Cleanup: removed {len(to_delete)} inactive sessions")
