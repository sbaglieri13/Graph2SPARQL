import os

# Usa l'endpoint passato via argomento, altrimenti fallback su DBpedia
RDF_STORE_ENDPOINT = os.getenv("SPARQL_ENDPOINT", "https://dbpedia.org/sparql")
