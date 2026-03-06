"""
Memory Manager - Gestion de la mémoire conversationnelle par user_id

Stockage historique et nettoyage automatique des sessions inactives
(Pattern aligné sur le projet AAA)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Stockage global mémoire (user_id -> {history: [{A, B}], last_active})
conversation_memory: Dict[str, Dict[str, Any]] = {}


def build_chat_history(history_pairs: List[Dict[str, str]]):
    """
    Convert stored history into role-based messages for the agent.
    history_pairs: list of {"A": user_message, "B": assistant_message}
    """
    chat_history = []
    for pair in history_pairs:
        chat_history.append({"role": "user", "content": pair["A"]})
        chat_history.append({"role": "assistant", "content": pair["B"]})
    return chat_history


async def cleanup_task(
    inactivity_timeout: timedelta,
    check_interval: int
):
    """
    Tâche asynchrone de nettoyage des sessions inactives.
    """
    logger.info(f"🧹 Cleanup task started (timeout={inactivity_timeout}, interval={check_interval}s)")

    while True:
        await asyncio.sleep(check_interval)

        now = datetime.utcnow()
        to_delete = [
            uid for uid, session in conversation_memory.items()
            if now - session.get("last_active", now) > inactivity_timeout
        ]

        for uid in to_delete:
            del conversation_memory[uid]
            logger.info(f"🗑️ Session {uid} deleted due to inactivity at {datetime.utcnow()}")

        if to_delete:
            logger.info(f"Cleanup: removed {len(to_delete)} inactive sessions")
