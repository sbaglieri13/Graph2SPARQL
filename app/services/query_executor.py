from SPARQLWrapper import SPARQLWrapper, JSON
from typing import List, Dict, Union
from app.utils.config_loader import load_sparql_config

config = load_sparql_config()
endpoint = config.get("endpoint", "https://dbpedia.org/sparql")


def execute_sparql_query(query: str, endpoint: str = None) -> Union[List[Dict], None]:
    if not endpoint:
        config = load_sparql_config()
        endpoint = config.get("endpoint", "https://dbpedia.org/sparql")

    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        return results["results"]["bindings"]
    except Exception as e:
        print(f"[SPARQL Error] {e}")
        return None



def sparql_to_graphql(results: List[Dict]) -> List[Dict]:
    """
    Converte i risultati SPARQL (bindings) in formato compatibile con GraphQL.
    """
    formatted_results = []

    for result in results:
        entry = {key: value["value"] for key, value in result.items()}
        formatted_results.append(entry)

    return formatted_results
