import yaml
from pathlib import Path
import os

def load_sparql_config(rdf_store: str = "default") -> dict:
    config_path = Path(__file__).resolve().parents[2] / "app/config/sparql_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    env_endpoint = os.getenv("SPARQL_ENDPOINT")
    if env_endpoint:
        config[rdf_store]["endpoint"] = env_endpoint

    return config.get(rdf_store, config)
