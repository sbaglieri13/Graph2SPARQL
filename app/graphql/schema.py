from ariadne import make_executable_schema, QueryType
from app.services.query_executor import execute_sparql_query
from app.utils.config_loader import load_sparql_config
from app.services.aggregate import graphql_aggregate_entities
from app.services.compare import graphql_compare_entities
from app.services.entity_search import resolve_search_entity

query = QueryType()
CONFIG = load_sparql_config()

@query.field("availableClasses")
def resolve_available_classes(*_, namespaceFilter: str = None):
    config = load_sparql_config()
    endpoint = config["endpoint"]

    rdf_type = config.get("rdf_type_property", "a")
    type_triple = f"?s {rdf_type} ?class ." if rdf_type != "a" else "?s a ?class ."

    sparql_query = f"""
    SELECT DISTINCT ?class WHERE {{
        {type_triple}
    }}
    """

    print("\nGenerated SPARQL Query:\n", sparql_query)
    sparql_results = execute_sparql_query(sparql_query, endpoint)
    if not sparql_results:
        return []

    classes = [result["class"]["value"] for result in sparql_results if "class" in result]

    if namespaceFilter:
        namespaceFilter = namespaceFilter.lower()
        classes = [cls for cls in classes if namespaceFilter in cls.lower()]

    return classes


@query.field("availableProperties")
def resolve_available_properties(*_, className: str):
    config = load_sparql_config()
    endpoint = config["endpoint"]

    rdf_type = config.get("rdf_type_property", "a")
    type_triple = f"?s {rdf_type} <{className}> ;" if rdf_type != "a" else f"?s a <{className}> ;"

    sparql_query = f"""
    SELECT DISTINCT ?property WHERE {{
        {type_triple}
        ?property ?o .
    }}
    """

    print("\nGenerated SPARQL Query:\n", sparql_query)
    sparql_results = execute_sparql_query(sparql_query, endpoint)

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
def graphql_search_entity(_, info, className: str, filters: list = None, optionalFilters: list = None,
                          unions: list = None, orderBy: list = None, groupBy: list = None, having: list = None,
                          notExistsFilters: list = None, existsFilters: list = None, selectFields: list = None,
                          distinct: bool = False, limit: int = None, offset: int = None):
    results = resolve_search_entity(className, filters, optionalFilters, unions, orderBy, groupBy, having,
                                    notExistsFilters, existsFilters, selectFields, distinct, limit, offset)
    return results


@query.field("aggregateEntities")
def resolve_aggregate_entities(_, info, **kwargs):
    return graphql_aggregate_entities(_, info, **kwargs)


@query.field("compareEntities")
def resolve_compare_entities(_, info, **kwargs):
    return graphql_compare_entities(_, info, **kwargs)


type_defs = """
    scalar JSON

    type Query {
        availableClasses(namespaceFilter: String): [String!]
        availableProperties(className: String!): GraphQLTypeInfo
        searchEntity(
            className: String,
            selectFields: [String],
            filters: [FilterInput],
            optionalFilters: [FilterInput],
            notExistsFilters: [FilterInput],
            existsFilters: [FilterInput],
            unions: [[FilterInput]],
            orderBy: [OrderByInput],
            groupBy: [String],
            having: [String],
            distinct: Boolean,
            limit: Int,
            offset: Int
        ): [JSON]
        aggregateEntities(
            className: String
            groupBy: String!
            aggregation: AggregationInput!
            having: [String]
            orderBy: [OrderByInput]
            limit: Int
            offset: Int
        ): [JSON]
        compareEntities(
            subjects: [SubjectInput!]!,
            paths: [JoinPathInput!]!,
            filters: [String],
            selectVars: [String!]
            limit: Int,
            offset: Int
        ): [JSON]
    }

    input AggregationInput {
        function: String!  
        alias: String!     
        on: String         
    }


    input SubjectInput {
        alias: String!
        className: String!
    }

    input JoinPathInput {
        from: String!
        path: [String!]!
        alias: String!
    }

    input FilterInput {
        property: String
        value: JSON
        operator: String
        path: [FilterPathStep]
    }

    input FilterPathStep {
        property: String!
        value: JSON
        operator: String
    }

    input OrderByInput {
        property: String!
        order: String!
    }

    type GraphQLTypeInfo {
        className: String
        fields: [String]
    }
"""

schema = make_executable_schema(type_defs, query)
