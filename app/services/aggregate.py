from SPARQLWrapper import SPARQLWrapper, JSON
from app.utils.config_loader import load_sparql_config
from app.utils.uri_utils import uri_to_var

def graphql_aggregate_entities(_, info, groupBy: str, aggregation: dict, having: list = None, orderBy: list = None, limit: int = None, offset: int = None, className: str = None):
    config = load_sparql_config()
    syntax = config["aggregation_syntax"]
    prefixes = "\n".join([f"PREFIX {k}: <{v}>" for k, v in config["prefixes"].items()])

    group_var = uri_to_var(groupBy)
    main_pattern = f"?s <{groupBy}> {group_var} ."

    if className:
        main_pattern = f"?s a <{className}> . " + main_pattern

    agg_property = aggregation.get("on", "*")
    agg_varname = "*" if agg_property == "*" else uri_to_var(agg_property)

    if agg_property != "*":
        triple = syntax["property_format"].format(subject="?s", property=agg_property, object=agg_varname)
        if triple not in main_pattern:
            main_pattern += f" {triple}"

    agg = syntax["aggregation_format"].format(
        function=aggregation["function"],
        variable=agg_varname,
        alias=aggregation["alias"]
    )
    select = syntax["select_format"].format(
        group_var=group_var,
        aggregations=agg,
        main_pattern=main_pattern
    )

    if having:
        having_expr = []
        alias = aggregation["alias"]
        function = aggregation["function"]
        agg_on = aggregation.get("on", "*")
        var_expr = f"{function}({uri_to_var(agg_on)})" if agg_on != "*" else f"{function}(*)"

        for cond in having:
            having_expr.append(cond.replace(f"?{alias}", var_expr))

        select += "\n" + syntax["having"].format(having_conditions=" && ".join(having_expr))

    if orderBy:
        order_clauses = []
        for item in orderBy:
            var = uri_to_var(item["property"])
            clause = f"{item['order'].upper()}({var})"
            order_clauses.append(clause)
        select += "\n" + syntax["order_by"].format(order_by_conditions=" ".join(order_clauses))

    if limit is not None:
        select += "\n" + syntax["limit"].format(limit=limit)
    if offset is not None:
        select += "\n" + syntax["offset"].format(offset=offset)

    sparql = SPARQLWrapper(config["endpoint"])
    sparql.setQuery(f"{prefixes}\n{select}")
    sparql.setReturnFormat(JSON)

    print("\nGenerated SPARQL Query:\n", f"{prefixes}\n{select}")
    results = sparql.query().convert()
    return results["results"]["bindings"]
