from SPARQLWrapper import SPARQLWrapper, JSON
from config import RDF_STORE_ENDPOINT as endpoint

def get_classes():
    """
    Recupera tutte le classi RDF disponibili nel dataset RDF.
    """
    sparql = SPARQLWrapper(endpoint)
    
    query = """

    SELECT DISTINCT ?class WHERE {
      ?s rdf:type ?class .
    }
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    classes = [res["class"]["value"] for res in results["results"]["bindings"]]
    return classes

def get_properties(rdf_class):
    """
    Recupera tutte le proprietà di una determinata classe RDF.
    """
    sparql = SPARQLWrapper(endpoint)
    
    query = f"""

    SELECT DISTINCT ?property WHERE {{
      ?s rdf:type <{rdf_class}> ;
         ?property ?o .
    }}
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    properties = [res["property"]["value"] for res in results["results"]["bindings"]]
    return properties

def generate_graphql_type(rdf_class):
    """
    Genera dinamicamente un tipo GraphQL con tutte le proprietà RDF della classe.
    """
    properties = get_properties(rdf_class)
    fields = {}

    for prop in properties:
        field_name = prop.split("/")[-1]  
        fields[field_name] = "String"  

    fields_str = "\n".join(f"{name}: {type_}" for name, type_ in fields.items())

    graphql_type = "type {class_name} {{\n{fields}\n}}".format(
        class_name=rdf_class.split("/")[-1],
        fields=fields_str
    )

    return graphql_type
