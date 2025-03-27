from SPARQLWrapper import SPARQLWrapper, JSON
from app.utils.config_loader import load_sparql_config

def graphql_compare_entities(_, info, subjects: list, paths: list, filters: list = None, selectVars: list = None):
    config = load_sparql_config()
    syntax = config["compare_syntax"]
    prefixes = "\n".join([f"PREFIX {k}: <{v}>" for k, v in config["prefixes"].items()])

    def alias_to_var(alias):
        import re
        alias = re.sub(r"[^a-zA-Z0-9_]", "_", alias)
        return f"?{alias}"

    subject_blocks = ""
    for s in subjects:
        var = alias_to_var(s["alias"])
        triple = syntax["subject_format"].format(var=var, class_uri=s["className"])
        subject_blocks += f"{triple} "

    path_blocks = ""
    for p in paths:
        current_var = alias_to_var(p["from"])
        for i, prop in enumerate(p["path"]):
            next_var = alias_to_var(p["alias"]) if i == len(p["path"]) - 1 else f"?{p['alias']}_step{i}"
            triple = syntax["property_format"].format(subject=current_var, property=prop, object=next_var)
            path_blocks += f"{triple} "
            current_var = next_var

    filter_conditions = ""
    if filters:
        for cond in filters:
            filter_conditions += syntax["filter_format"].format(condition=cond) + " "

    select_clause = " ".join(selectVars) if selectVars else "*"
    query = syntax["select_format"].format(
        select_vars=select_clause,
        subject_blocks=subject_blocks,
        path_blocks=path_blocks,
        filter_conditions=filter_conditions
    )

    sparql = SPARQLWrapper(config["endpoint"])
    sparql.setQuery(f"{prefixes}\n{query}")
    sparql.setReturnFormat(JSON)

    print("\nGenerated SPARQL Query:\n", f"{prefixes}\n{query}")
    results = sparql.query().convert()

    output = []
    for result in results["results"]["bindings"]:
        entry = {}
        for var in result:
            entry[var] = result[var]["value"]
        output.append(entry)
    return output
