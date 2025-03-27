import re

def uri_to_safe_var(uri: str) -> str:
    name = uri.split("/")[-1]
    if "#" in name:
        name = name.split("#")[-1]
    safe_name = re.sub(r'\W|^(?=\d)', '_', name)
    return f"var_{safe_name}"

                    
def uri_to_var(uri: str) -> str:
    name = re.split(r"[#/]", uri)[-1]
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    return f"?{name}"