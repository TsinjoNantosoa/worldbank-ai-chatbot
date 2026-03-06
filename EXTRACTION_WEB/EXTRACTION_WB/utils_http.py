"""
HTTP Utilities - Session avec retries et timeouts

Wrapper pour requests.Session avec gestion d'erreurs robuste
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


def create_session_with_retries(
    retries: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: tuple = (500, 502, 503, 504),
    timeout: int = 30
) -> requests.Session:
    """
    Crée une session requests avec retries automatiques
    
    Args:
        retries: Nombre de tentatives
        backoff_factor: Facteur exponentiel entre retries
        status_forcelist: Codes HTTP à retry
        timeout: Timeout par défaut (secondes)
        
    Returns:
        Session configurée
    """
    session = requests.Session()
    
    # Configuration retry strategy
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    # Adapter avec retry
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Headers par défaut
    session.headers.update({
        'User-Agent': 'WorldBankDataCollector/1.0 (Educational Project)',
        'Accept': 'application/json'
    })
    
    logger.debug(f"Created session with {retries} retries, backoff={backoff_factor}")
    
    return session
