from SPARQLWrapper import SPARQLWrapper, JSON
from config import RDF_STORE_ENDPOINT as endpoint

def execute_sparql_query(query: str):
    """
    Esegue una query SPARQL su DBpedia e restituisce i risultati in formato JSON.
    """
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    

    try:
        results = sparql.query().convert()
        return results["results"]["bindings"]
    except Exception as e:
        return {"error": str(e)}

def sparql_to_graphql(results):
    """
    Converte i risultati SPARQL in un formato JSON compatibile con GraphQL.
    """
    formatted_results = []

    for result in results:
        formatted_entry = {}
        for key, value in result.items():
            formatted_entry[key] = value["value"]  
        formatted_results.append(formatted_entry)

    return formatted_results
