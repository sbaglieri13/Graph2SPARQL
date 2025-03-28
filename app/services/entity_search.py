from app.utils.config_loader import load_sparql_config
from app.utils.uri_utils import uri_to_safe_var
from SPARQLWrapper import SPARQLWrapper, JSON
import re

def resolve_search_entity(entity_class, filters=None, optionalFilters=None, unions=None, orderBy=None, groupBy=None, having=None, notExistsFilters=None, existsFilters=None, selectFields=None, distinct=False, limit=None, offset=None, rdf_store="default"):
    config = load_sparql_config(rdf_store)
    options = config["options"]
    syntax = config["query_syntax"]

    prefixes = "\n".join([f"PREFIX {k}: <{v}>" for k, v in config["prefixes"].items()])
    modifiers = "DISTINCT " if distinct else ""

    main_pattern = " ".join([p.format(class_uri=entity_class) for p in options.get("main_patterns", [])])   
    
    entity_alias = entity_class.split("/")[-1].lower()

    if selectFields is not None:
        if selectFields == []:
            select_vars = ["?s"]
            select_mappings = {"?s": entity_alias}
        else:
            select_vars = ["?s"]
            select_mappings = {"?s": entity_alias}
            for field in selectFields:
                safe_var = uri_to_safe_var(field)
                var = f"?{safe_var}"

                triple = syntax["property_format"].format(subject="?s", property=field, object=var)
                if triple not in main_pattern:
                    main_pattern += f" {triple}"
                select_vars.append(var)
                select_mappings[var] = field.split('/')[-1]
    else:
        select_vars = ["*"]
        select_mappings = {"?s": entity_alias}

    optional_patterns = " ".join([syntax["optional_format"].format(pattern=p) for p in options.get("optional_patterns", [])])
    filter_conditions = " ".join([syntax["filter_format"].format(condition=c) for c in options.get("filter_conditions", [])])

    generated_paths = set()

    if filters:
        for f in filters:
            if "path" in f:
                path = f["path"]
                prev_var = "?s"
                for i, step in enumerate(path):
                    prop = step["property"]
                    safe_var = uri_to_safe_var(prop)
                    var = f"?var_step_{i}_{safe_var[4:]}"  

                    triple = syntax["property_format"].format(subject=prev_var, property=prop, object=var)

                    if triple not in main_pattern:
                        main_pattern += f" {triple}"
                        generated_paths.add(triple.strip())

                    if "value" in step:
                        op = step.get("operator", "=")
                        op_template = config.get("operator_map", {}).get(op)
                        if op_template:
                            val = step["value"]
                            if isinstance(val, str) and val.startswith("http"):
                                value_formatted = f'<{val}>'
                            elif re.match(r'^.+@[\w\-]+$', val):  
                                literal, lang = val.rsplit("@", 1)
                                value_formatted = f'"{literal}"@{lang}'
                            elif op in [">", "<", ">=", "<="]:
                                value_formatted = f'"{val}"^^xsd:date'
                            else:
                                value_formatted = f'"{val}"'
                            condition = op_template.format(var=var, value=value_formatted)
                            filter_conditions += " " + syntax["filter_format"].format(condition=condition)

                    prev_var = var
            else:

                prop = f["property"]
                val = f["value"]
                op = f.get("operator", "=")

                var = f"?{uri_to_safe_var(prop)}"

                triple = syntax["property_format"].format(subject="?s", property=prop, object=var)

                if triple not in main_pattern:
                    main_pattern += f" {triple}"
                    generated_paths.add(triple.strip())

                op_template = config.get("operator_map", {}).get(op)
                if op_template:
                    if isinstance(val, str) and val.startswith("http"):
                        value_formatted = f'<{val}>'
                    elif re.match(r'^.+@[\w\-]+$', val):  
                        literal, lang = val.rsplit("@", 1)
                        value_formatted = f'"{literal}"@{lang}'
                    elif op in [">", "<", ">=", "<="]:
                        value_formatted = f'"{val}"^^xsd:date'
                    else:
                        value_formatted = f'"{val}"'
                    condition = op_template.format(var=var, value=value_formatted)
                    filter_conditions += " " + syntax["filter_format"].format(condition=condition)


    if optionalFilters:
        for f in optionalFilters:
            prop = f["property"]
            var = f"?{uri_to_safe_var(prop)}"

            triple = syntax["property_format"].format(subject="?s", property=prop, object=var)
            optional_patterns += " " + syntax["optional_format"].format(pattern=triple)

    not_exists_patterns = ""
    if notExistsFilters:
        for f in notExistsFilters:
            if "path" in f:
                path = f["path"]
                prev_var = "?s"
                pattern = ""
                for i, step in enumerate(path):
                    prop = step["property"]
                    safe_var = uri_to_safe_var(prop)
                    var = f"?var_step_{i}_{safe_var[4:]}"  

                    triple = syntax["property_format"].format(subject=prev_var, property=prop, object=var).strip()

                    if triple not in generated_paths:
                        pattern += f"{triple} "

                    prev_var = var

                if pattern:
                    not_exists_patterns += f"FILTER NOT EXISTS {{ {pattern}}} "

    exists_patterns = ""
    if existsFilters:
        for f in existsFilters:
            if "path" in f:
                path = f["path"]
                prev_var = "?s"
                pattern = ""
                for i, step in enumerate(path):
                    prop = step["property"]
                    safe_var = uri_to_safe_var(prop)
                    var = f"?var_step_{i}_{safe_var[4:]}"  

                    triple = syntax["property_format"].format(subject=prev_var, property=prop, object=var).strip()

                    if triple not in generated_paths:
                        pattern += f"{triple} "

                    prev_var = var

                if pattern:
                    exists_patterns += f"FILTER EXISTS {{ {pattern}}} "

    union_blocks = ""
    if unions:
        union_templates = []
        for union_group in unions:
            block = " ".join([
                syntax["property_format"].format(subject="?s", property=f["property"], object=f'<{f["value"]}>')
                for f in union_group
            ])
            union_templates.append(syntax["union_format"].format(block=block))
        union_blocks = " UNION ".join(union_templates)

    order_by_clause = ""
    if orderBy:
        order_clauses = []
        for item in orderBy:
            prop = item["property"]
            direction = item["order"].upper()
            var = f"?{uri_to_safe_var(prop)}"

            triple = syntax["property_format"].format(subject="?s", property=prop, object=var)
            if triple not in main_pattern:
                main_pattern += f" {triple}"
            clause = syntax.get("order_clause_format", "{order}({var})").format(order=direction, var=var)
            order_clauses.append(clause)
        order_by_clause = "\n" + syntax["order_by"].format(order_by_conditions=" ".join(order_clauses))
    elif options.get("order_by_conditions"):
        order_by_clause = "\n" + syntax["order_by"].format(
            order_by_conditions=" ".join(options["order_by_conditions"])
        )

    query = syntax["select_format"].format(
        modifiers=modifiers,
        select_vars=" ".join(select_vars),
        main_pattern=main_pattern,
        optional_patterns=optional_patterns,
        union_blocks=union_blocks,
        filter_conditions=filter_conditions + " " + not_exists_patterns + " " + exists_patterns
    )+ order_by_clause

    if groupBy:
        group_vars = ["?s"]  
        for uri in groupBy:
            group_vars.append(f"?{uri_to_safe_var(uri)}")
        query += "\n" + syntax["group_by"].format(group_by_fields=" ".join(group_vars))
    elif options.get("group_by_fields"):
        query += "\n" + syntax["group_by"].format(group_by_fields=" ".join(options["group_by_fields"]))

    if having:
        query += "\n" + syntax["having"].format(having_conditions=" && ".join(having))
    elif options.get("having_conditions"):
        query += "\n" + syntax["having"].format(having_conditions=" && ".join(options["having_conditions"]))

    if options.get("group_by_fields"):
        query += "\n" + syntax["group_by"].format(
            group_by_fields=" ".join(options["group_by_fields"])
        )

    if options.get("having_conditions"):
        query += "\n" + syntax["having"].format(
            having_conditions=" && ".join(options["having_conditions"])
        )

    if options.get("order_by_conditions"):
        query += "\n" + syntax["order_by"].format(
            order_by_conditions=" ".join(options["order_by_conditions"])
        )

    if limit is not None:
        query += "\n" + syntax["limit"].format(limit=limit)

    if offset is not None:
        query += "\n" + syntax["offset"].format(offset=offset)

    sparql = SPARQLWrapper(config["endpoint"])
    sparql.setQuery(f"{prefixes}\n{query}")
    sparql.setReturnFormat(JSON)

    print("\nGenerated SPARQL Query:\n", f"{prefixes}\n{query}")
    results = sparql.query().convert()
    bindings = results["results"]["bindings"]
    
    output = []
    for result in bindings:
        entry = {}

        if select_vars == ["*"]:
            for var in result:
                varname = var
                if var == "s":
                    entry[entity_alias] = result[var]["value"]
                else:
                    pretty_name = var
                    if var.startswith("var_step_"):
                        pretty_name = var.split("_")[-1]
                    elif var.startswith("var_"):
                        pretty_name = var.split("_", 1)[1]
                    entry[pretty_name] = result[var]["value"]
        elif select_mappings:
            for var, field_name in select_mappings.items():
                if var[1:] in result:
                    entry[field_name] = result[var[1:]]["value"]
        else:
            for var in result:
                entry[var] = result[var]["value"]

        output.append(entry)

    return output