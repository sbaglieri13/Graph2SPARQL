import uvicorn
import argparse
import os
from fastapi import FastAPI
from app.graphql.schema import schema
from ariadne.asgi import GraphQL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Avvia il server GraphQL con un endpoint SPARQL configurabile.")
parser.add_argument("--endpoint", type=str, default="https://dbpedia.org/sparql",
                    help="Specifica l'endpoint SPARQL (default: DBpedia)")
args = parser.parse_args()

os.environ["SPARQL_ENDPOINT"] = args.endpoint

app = FastAPI()

graphql_app = GraphQL(schema, debug=True)
app.add_route("/graphql", graphql_app)


@app.get("/")
def read_root():
    return {"message": "GraphQL to SPARQL API is running!", "SPARQL Endpoint": os.getenv("SPARQL_ENDPOINT")}


if __name__ == "__main__":
    logger.info("Avvio del server FastAPI...")
    logger.info(f"SPARQL Endpoint configurato: {os.getenv('SPARQL_ENDPOINT')}")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
