"""
Configuration Loader - Charge config.json et variables d'environnement

Gestion centralisée de la configuration avec overrides par env vars
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Charge la configuration depuis JSON avec overrides par variables d'environnement
    
    Args:
        config_path: Chemin fichier config.json
        
    Returns:
        Dict configuration fusionnée
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults + env vars")
        config = _get_default_config()
    else:
        logger.info(f"Loading config from {config_path}")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # Override avec variables d'environnement
    config = _apply_env_overrides(config)
    
    # Validation
    _validate_config(config)
    
    return config


def _get_default_config() -> Dict[str, Any]:
    """Configuration par défaut"""
    return {
        "model": "gpt-4o-mini",
        "embedding_model": "text-embedding-3-large",
        "data_file": "data/world_bank_data.json",
        "max_pairs": 5,
        "inactivity_timeout_minutes": 5,
        "inactivity_check_interval_seconds": 300,
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "reload": False
        }
    }


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applique overrides depuis variables d'environnement
    
    Env vars supportées:
    - OPENAI_API_KEY
    - WB_MODEL
    - WB_EMBEDDING_MODEL
    - WB_DATA_FILE
    - WB_SERVER_HOST
    - WB_SERVER_PORT
    """
    # OpenAI API Key (priorité env var)
    if "OPENAI_API_KEY" in os.environ:
        config["openai_api_key"] = os.environ["OPENAI_API_KEY"]
        logger.info("Using OPENAI_API_KEY from environment")
    
    # Model overrides
    if "WB_MODEL" in os.environ:
        config["model"] = os.environ["WB_MODEL"]
    
    if "WB_EMBEDDING_MODEL" in os.environ:
        config["embedding_model"] = os.environ["WB_EMBEDDING_MODEL"]
    
    if "WB_DATA_FILE" in os.environ:
        config["data_file"] = os.environ["WB_DATA_FILE"]
    
    # Server config
    if "WB_SERVER_HOST" in os.environ:
        config.setdefault("server", {})["host"] = os.environ["WB_SERVER_HOST"]
    
    if "WB_SERVER_PORT" in os.environ:
        config.setdefault("server", {})["port"] = int(os.environ["WB_SERVER_PORT"])
    
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Valide la configuration
    
    Raises:
        ValueError: Si config invalide
    """
    # OpenAI API key obligatoire
    if not config.get("openai_api_key"):
        raise ValueError(
            "OpenAI API key not found! Set in config.json or OPENAI_API_KEY env var"
        )
    
    # Data file doit exister ou être créable
    data_file = Path(config.get("data_file", "data/world_bank_data.json"))
    if not data_file.exists():
        logger.warning(f"Data file not found: {data_file}")
        # Créer dossier parent si nécessaire
        data_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Autres validations
    required_keys = ["model", "embedding_model"]
    missing = [k for k in required_keys if k not in config]
    
    if missing:
        raise ValueError(f"Missing required config keys: {missing}")
    
    logger.info("✅ Configuration validated")


def get_config_value(config: Dict, key: str, default: Any = None) -> Any:
    """
    Récupère une valeur de config avec gestion sécurisée
    
    Args:
        config: Dict configuration
        key: Clé (support notation pointée ex: 'server.host')
        default: Valeur par défaut
        
    Returns:
        Valeur ou default
    """
    keys = key.split('.')
    value = config
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
    
    return value if value is not None else default
