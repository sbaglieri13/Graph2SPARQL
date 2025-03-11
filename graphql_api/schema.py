from ariadne import make_executable_schema, QueryType, ObjectType
from middleware.query_executor import execute_sparql_query

query = QueryType()

@query.field("availableClasses")
def resolve_available_classes(*_):
    """
    Recupera tutte le classi RDF disponibili e restituisce i link completi.
    """
    sparql_query = """
    SELECT DISTINCT ?class WHERE {
        ?s a ?class .
    }
    """
    print("\nGenerated SPARQL Query:\n", sparql_query)
    sparql_results = execute_sparql_query(sparql_query)

    if not sparql_results:
        return []

    return [result["class"]["value"] for result in sparql_results if "class" in result]


@query.field("getDynamicGraphQLType")
def resolve_get_dynamic_graphql_type(*_, className: str):
    """
    Ottiene dinamicamente la struttura GraphQL di una classe RDF con le proprietà complete.
    """
    sparql_query = f"""
    SELECT DISTINCT ?property WHERE {{
        ?s a <{className}> ;
           ?property ?o .
    }}
    """
    print("\nGenerated SPARQL Query:\n", sparql_query)
    sparql_results = execute_sparql_query(sparql_query)

    if not sparql_results:
        return None

    properties = set()  
    for result in sparql_results:
        if "property" in result:
            properties.add(result["property"]["value"])

    return {
        "className": className,
        "fields": list(properties)
    }



@query.field("searchEntity")
def resolve_search_entity(
    _, info, className: str, filters: list = None, optionalFilters: list = None, 
    unions: list = None, orderBy: list = None, distinct: bool = False, limit: int = None, offset: int = None
):
    """
    Genera una query SPARQL dinamica per qualsiasi classe RDF, supportando:
    - Filtri (FILTER)
    - Condizioni opzionali (OPTIONAL)
    - UNION
    - ORDER BY
    - DISTINCT, LIMIT, OFFSET
    """
    
    sparql_query = f"""
    SELECT {'DISTINCT' if distinct else ''} ?entity WHERE {{
        ?entity a <{className}> .
    """

    filter_conditions = []
    extra_triples = []  

    if filters:
        for filter in filters:
            prop, val, op = filter["property"], filter["value"], filter.get("operator", "=")
            var_name = f"?var_{prop.split('/')[-1]}"  

            if isinstance(val, list): 
                values_list = " ".join([f"<{v}>" for v in val])
                sparql_query += f"\n    VALUES {var_name} {{ {values_list} }}"
                if f"?entity <{prop}> {var_name} ." not in sparql_query:
                    sparql_query += f"\n    ?entity <{prop}> {var_name} ."

            elif op in [">=", "<=", ">", "<", "!="]:  
                if f"?entity <{prop}> {var_name} ." not in extra_triples:
                    extra_triples.append(f"?entity <{prop}> {var_name} .")

                if "birthDate" in prop or "date" in prop:
                    filter_conditions.append(f"{var_name} {op} \"{val}\"^^xsd:date")
                else:
                    filter_conditions.append(f"{var_name} {op} \"{val}\"")
            else:   
                sparql_query += f"\n    ?entity <{prop}> \"{val}\" ."

    for triple in extra_triples:
        sparql_query += f"\n    {triple}"

    if filter_conditions:
        sparql_query += f"\n    FILTER({' && '.join(filter_conditions)})"

    if optionalFilters:
        for filter in optionalFilters:
            prop, val = filter["property"], filter["value"]
            sparql_query += f"\n    OPTIONAL {{ ?entity <{prop}> <{val}> . }}"

    if unions:
        union_query = []
        for union_group in unions:
            union_block = " ".join([f"?entity <{f['property']}> \"{f['value']}\" ." for f in union_group])
            union_query.append(f"{{ ?entity a <{className}> . {union_block} }}")
        sparql_query += "\n    " + " UNION ".join(union_query)

    sparql_query += "\n}"  

    order_by_clause = ""
    if orderBy:
        for order in orderBy:
            prop = order["property"]
            order_direction = order["order"]
            var_name = f"?var_{prop.split('/')[-1]}"  

            if f"?entity <{prop}> {var_name} ." not in sparql_query:
                sparql_query = sparql_query.replace("\n}", f"\n    ?entity <{prop}> {var_name} .\n}}")

            order_by_clause = f"\nORDER BY {order_direction}({var_name})"

    sparql_query += order_by_clause  

    if limit:
        sparql_query += f"\nLIMIT {limit}"
    if offset:
        sparql_query += f"\nOFFSET {offset}"

    print("\nGenerated SPARQL Query:\n", sparql_query)

    results = execute_sparql_query(sparql_query)

    return [{"uri": result["entity"]["value"]} for result in results] if results else []



type_defs = """
    type Query {
        availableClasses(namespaceFilter: String): [String!]
        getDynamicGraphQLType(className: String!): GraphQLTypeInfo
        searchEntity(
            className: String,
            filters: [FilterInput], 
            optionalFilters: [FilterInput], 
            unions: [[FilterInput]],  # Liste di liste per UNION
            orderBy: [OrderByInput],
            distinct: Boolean, 
            limit: Int,
            offset: Int
        ): [Entity]
    }

    type Entity {
        uri: String
    }

    input FilterInput {
        property: String!
        value: JSON  
        operator: String  # Supporta "=", "!=", ">", "<", ">=", "<="
    }

    input OrderByInput {
        property: String!
        order: String!  # "ASC" o "DESC"
    }

    type GraphQLTypeInfo {
        className: String
        fields: [String]
    }

    scalar JSON  

"""


schema = make_executable_schema(type_defs, query)
