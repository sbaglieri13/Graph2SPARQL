import uvicorn
from fastapi import FastAPI
from graphql_api.schema import schema  
from ariadne.asgi import GraphQL

app = FastAPI()

graphql_app = GraphQL(schema, debug=True)
app.add_route("/graphql", graphql_app)

@app.get("/")
def read_root():
    return {"message": "Graph2SPARQL API is running!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
