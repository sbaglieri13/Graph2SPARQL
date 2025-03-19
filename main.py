import uvicorn
import argparse
import os
from fastapi import FastAPI
from graphql_api.schema import schema  # Importiamo lo schema GraphQL
from ariadne.asgi import GraphQL

# Parser per argomenti da riga di comando
parser = argparse.ArgumentParser(description="Avvia il server GraphQL con un endpoint SPARQL configurabile.")
parser.add_argument("--endpoint", type=str, default="https://dbpedia.org/sparql", help="Specifica l'endpoint SPARQL (default: DBpedia)")
args = parser.parse_args()

# Imposta l'endpoint come variabile d'ambiente per renderlo disponibile in tutto il progetto
os.environ["SPARQL_ENDPOINT"] = args.endpoint



# Creiamo l'app FastAPI
app = FastAPI()

# Integriamo Ariadne con FastAPI
graphql_app = GraphQL(schema, debug=True)
app.add_route("/graphql", graphql_app)

# Endpoint di test
@app.get("/")
def read_root():
    return {"message": "GraphQL to SPARQL API is running with Ariadne!", "SPARQL Endpoint": os.getenv("SPARQL_ENDPOINT")}

# Avvio del server
if __name__ == "__main__":
    print("🚀 Avvio del server FastAPI...")
    # Log dell'endpoint selezionato
    print(f"🔗 SPARQL Endpoint configurato: {os.getenv('SPARQL_ENDPOINT')}")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    