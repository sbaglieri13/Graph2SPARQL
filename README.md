# Graph2SPARQL

**Graph2SPARQL** è un server GraphQL che traduce dinamicamente query GraphQL in query SPARQL, permettendo di interrogare qualsiasi RDF store configurato tramite un file YAML.

L’obiettivo del progetto è fornire un’interfaccia di interrogazione GraphQL per accedere a knowledge base strutturate in RDF (come DBpedia, Wikidata o dataset custom), senza richiedere all’utente di conoscere la sintassi SPARQL, e mascherare la complessità di SPARQL dietro una sintassi
GraphQL più semplice

## Funzionalità principali

- **Endpoint GraphQL unico** per interrogare dataset RDF.
- **Traduzione automatica** delle query GraphQL in SPARQL.
- **Configurazione dinamica via YAML**: supporto a più endpoint SPARQL semplicemente modificando il file `sparql_config.yaml`.
- **Supporto ai principali costrutti SPARQL**:
  - `FILTER`, `OPTIONAL`, `FILTER NOT EXISTS`, `FILTER EXISTS`, `UNION`
  - `ORDER BY`, `GROUP BY`, `HAVING`, `LIMIT`, `OFFSET`
- **Funzioni di aggregazione supportate**:
  - `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`
- **Navigazione lungo path RDF arbitrari**, anche su più salti (`?film dbo:director ?d . ?d dbo:birthPlace ?city`).
- **Personalizzazione completa della sintassi SPARQL**, operatori, prefissi, variabili e output tramite YAML.

## Avvio del server

### 1. Requisiti

Assicurati di avere installato:

- **Python** 3.9 o superiore
- Le seguenti dipendenze Python:
  - `uvicorn`
  - `fastapi`
  - `ariadne`
  - `pyyaml`
  - `SPARQLWrapper`

Installa tutto con:

```bash
pip install -r requirements.txt
```

---

### 2. Avvio standard (utilizzando DBpedia)

Se non specifichi un endpoint, il sistema userà quello definito come `default` in `sparql_config.yaml`.

```bash
python server.py
```

GraphQL Playground sarà disponibile su: [http://127.0.0.1:8000/graphql](http://127.0.0.1:8000/graphql)

---

### 3. Avvio con endpoint personalizzato

Puoi usare un qualsiasi SPARQL endpoint (es. Wikidata):

```bash
python server.py --endpoint "https://query.wikidata.org/sparql"
```

Il server userà questo endpoint temporaneamente, senza modificare il file YAML. In questo caso occorrerà procedere con la modifica del file di configurazione `sparql_config.yaml` per far si che il tutto funzioni correttamente con il nuovo endpoint SPARQL. 

Per maggiori dettagli sul file di configurazione consulta la sezione `File di configurazione sparql_config.yaml`, mentre per il cambio RDF Store consulta la sezione `Cambio RDF store a runtime`.


## Struttura del progetto
 
Di seguito una panoramica della struttura del progetto:

```
Graph2SPARQL/
├── server.py                  # Entry point: avvia il server e gestisce l'endpoint SPARQL
├── requirements.txt           # Dipendenze Python del progetto
├── app/
│   ├── graphql/
│   │   └── schema.py          # Definizione dello schema GraphQL
│   ├── services/
│   │   ├── entity_search.py   # Logica per searchEntity
│   │   ├── aggregate.py       # Logica per aggregateEntities
│   │   └── compare.py         # Logica per compareEntities
│   │   └── query_executor.py  # Esecuzione delle query SPARQL
│   ├── utils/
│   │   ├── config_loader.py   # Caricamento e parsing del file YAML
│   │   └── uri_utils.py       # Utility per nomi variabili SPARQL e gestione URI
│   └── config/
│       └── sparql_config.yaml # Configurazione dell’endpoint, sintassi e mapping
```

## File di configurazione `sparql_config.yaml`

Il file `sparql_config.yaml` (in `app/config/`) consente di personalizzare completamente il comportamento del sistema per adattarsi a **qualsiasi RDF store**, senza modificare il codice Python.

---

### Struttura base

```yaml
default:
  endpoint: "https://dbpedia.org/sparql"
  prefixes:
    rdf: "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    rdfs: "http://www.w3.org/2000/01/rdf-schema#"
    dbo: "http://dbpedia.org/ontology/"
    dbp: "http://dbpedia.org/property/"
```

- `default`: nome del profilo di configurazione.
- `endpoint`: URL dell’endpoint SPARQL.
- `prefixes`: dizionario dei prefissi da usare nelle query.

---

### `query_syntax` – Struttura delle query

Template per costruire query SPARQL dinamiche usate da `searchEntity`.

```yaml
query_syntax:
  select_format: |
    SELECT {modifiers}{select_vars} WHERE {{
      {main_pattern}
      {optional_patterns}
      {union_blocks}
      {filter_conditions}
    }}
  property_format: "{subject} <{property}> {object} ."
  optional_format: "OPTIONAL {{ {pattern} }}"
  union_format: "{{ {block} }}"
  filter_format: "FILTER ({condition})"
  group_by: "GROUP BY {group_by_fields}"
  having: "HAVING({having_conditions})"
  order_by: "ORDER BY {order_by_conditions}"
  limit: "LIMIT {limit}"
  offset: "OFFSET {offset}"
```

| Chiave              | Descrizione                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| `select_format`     | Template dell'intera query `SELECT`; usa segnaposti per pattern e filtri    |
| `property_format`   | Triple di base nella forma `soggetto - predicato - oggetto`                 |
| `optional_format`   | Template SPARQL per blocchi opzionali (`OPTIONAL { ... }`)                  |
| `union_format`      | Template SPARQL per blocchi `UNION`                                         |
| `filter_format`     | Template SPARQL per i filtri (`FILTER (...)`)                               |
| `group_by`          | Template per clausole `GROUP BY` con variabili                              |
| `having`            | Template per blocchi `HAVING`, usati con aggregazioni                       |
| `order_by`          | Template per clausole `ORDER BY`                                            |
| `limit`             | Limita il numero di risultati (`LIMIT n`)                                   |
| `offset`            | Offset per la paginazione (`OFFSET n`)                                      |

---

### `options` – Comportamenti dinamici

```yaml
options:
  use_distinct: false
  select_vars: ["?s"]
  main_patterns:
    - "?s a <{class_uri}> ."
  optional_patterns: []
  filter_conditions: []
  group_by_fields: []
  having_conditions: []
  order_by_conditions: []
```

| Chiave               | Descrizione |
|----------------------|-------------|
| `use_distinct`       | Aggiunge `DISTINCT` nel blocco SELECT |
| `select_vars`        | Variabili di default nel SELECT |
| `main_patterns`      | Triple SPARQL principali (usa `{class_uri}` come segnaposto) |
| `optional_patterns`  | Triple opzionali fisse |
| `filter_conditions`  | Filtri SPARQL fissi |
| `group_by_fields`    | Variabili di grouping fisse |
| `having_conditions`  | Condizioni fisse per blocco `HAVING` |
| `order_by_conditions`| Ordinamenti predefiniti |

---

### `operator_map` – Mappatura operatori

```yaml
operator_map:
  "=": "{var} = {value}"
  "!=": "{var} != {value}"
  ">": "{var} > {value}"
  "<": "{var} < {value}"
  ">=": "{var} >= {value}"
  "<=": "{var} <= {value}"
  REGEX: "REGEX({var}, {value}, \"i\")"
  LANG_EQUALS: "LANG({var}) = {value}"
```

| Operatore       | Descrizione                                          |
|------------------|------------------------------------------------------|
| `=`              | Uguaglianza tra variabile e valore                   |
| `!=`             | Disuguaglianza tra variabile e valore                |
| `>`              | Maggiore di                                          |
| `<`              | Minore di                                            |
| `>=`             | Maggiore o uguale a                                  |
| `<=`             | Minore o uguale a                                    |
| `REGEX`          | Confronto testuale con espressione regolare (insensibile al caso) |
| `LANG_EQUALS`    | Confronto tra lingua della variabile e valore (es. `"en"`) |

---

### `type_casting` – Tipi SPARQL

```yaml
type_casting:
  date: "^^xsd:date"
```

Serve per specificare il tipo SPARQL da usare per valori come date o numeri.

| Chiave | Descrizione |
|--------|-------------|
| `date` | Specifica che un valore deve essere trattato come `xsd:date`, utile per confronti con operatori come `>`, `<` |

---

### `aggregation_syntax` – Query aggregate

```yaml
aggregation_syntax:
  select_format: |
    SELECT {group_var} {aggregations} WHERE {{
      {main_pattern}
    }} GROUP BY {group_var}
  aggregation_format: "({function}({variable}) AS ?{alias})"
  group_by: "GROUP BY {group_var}"
  having: "HAVING({having_conditions})"
  order_by: "ORDER BY {order_by_conditions}"
  limit: "LIMIT {limit}"
  offset: "OFFSET {offset}"
  property_format: "{subject} <{property}> {object} ."
```

| Chiave               | Descrizione |
|----------------------|-------------|
| `select_format`      | Template principale della query aggregate |
| `aggregation_format` | Formato per ogni aggregazione (es. `SUM(?budget)`) |
| `group_by`           | Clausola `GROUP BY` con variabili specificate |
| `having`             | Condizioni sul risultato aggregato |
| `order_by`           | Ordinamento dei risultati aggregati |
| `limit`              | Numero massimo di risultati |
| `offset`             | Offset per la paginazione |
| `property_format`    | Formato delle triple SPARQL |

---

### `compare_syntax` – Confronto entità

```yaml
compare_syntax:
  select_format: |
    SELECT {select_vars} WHERE {{
      {subject_blocks}
      {path_blocks}
      {filter_conditions}
    }}
  subject_format: "{var} a <{class_uri}> ."
  property_format: "{subject} <{property}> {object} ."
  filter_format: "FILTER ({condition})"
```

| Chiave            | Descrizione |
|-------------------|-------------|
| `select_format`   | Struttura della query SPARQL per il confronto tra entità |
| `subject_format`  | Definizione del tipo RDF per ogni soggetto |
| `property_format` | Formato delle triple di relazione tra entità |
| `filter_format`   | Formato delle condizioni di filtro tra variabili |


---


## Esplorazione del dataset: classi e proprietà disponibili

Per orientarsi nel grafo RDF, Graph2SPARQL espone due metodi utili:

---

### `availableClasses`

Restituisce tutte le classi RDF presenti nel dataset interrogato, rilevate tramite la proprietà `rdf:type`.

È anche possibile filtrare i risultati specificando una stringa `namespaceFilter`, che restituisce solo le classi il cui URI contiene quella stringa (case-insensitive).

#### Parametri
- `namespaceFilter` (opzionale): stringa per filtrare solo le classi che contengono il termine specificato (case-insensitive)

#### Query SPARQL generata

```sparql
SELECT DISTINCT ?class WHERE {
  ?s a ?class .
}
```

#### Esempio di query GraphQL

```graphql
query {
  availableClasses(namespaceFilter: "film")
}
```

#### Risposta attesa

```json
[
  "http://dbpedia.org/ontology/Film",
  "http://schema.org/Film",
  ...
]
```

---

### `availableProperties`

Restituisce tutte le proprietà RDF direttamente collegate a una certa classe RDF, sotto forma di lista.

#### Parametri
- `className` (obbligatorio): URI della classe RDF di cui si vogliono esplorare le proprietà.

#### Query SPARQL generata

```sparql
SELECT DISTINCT ?property WHERE {
  ?s a <className> ;
     ?property ?o .
}
```

#### Esempio di query GraphQL

```graphql
query {
  availableProperties(className: "http://dbpedia.org/ontology/Film") {
    className
    fields
  }
}
```

#### Risposta attesa

```json
{
  "className": "http://dbpedia.org/ontology/Film",
  "fields": [
    "http://dbpedia.org/ontology/budget",
    "http://dbpedia.org/ontology/director",
    "http://dbpedia.org/ontology/releaseDate",
    ...
  ]
}
```

---

Questi metodi sono utili per esplorare il dataset RDF e permettono di costruire query corrette in `searchEntity`, `aggregateEntities` o `compareEntities` senza dover conoscere a priori tutte le classi e proprietà esistenti.


## Guida completa all'utilizzo delle query GraphQL

### `searchEntity`

Permette di interrogare una classe RDF specificando proprietà, filtri, path, aggregazioni e altro.

#### Parametri disponibili

| Parametro         | Tipo       | Descrizione                                                                 |
|-------------------|------------|-----------------------------------------------------------------------------|
| `className`       | String     | URI della classe RDF da interrogare (es. `dbo:Film`)                        |
| `selectFields`    | [String]   | URI delle proprietà RDF da includere nella SELECT                          |
| `filters`         | [Object]   | Filtro su proprietà dirette o su path multipli                             |
| `optionalFilters` | [Object]   | Proprietà opzionali (SPARQL `OPTIONAL`)                                    |
| `notExistsFilters`, `existsFilters` | [Object] | Pattern con `FILTER NOT EXISTS` e `FILTER EXISTS`                  |
| `distinct`        | Boolean    | Aggiunge `DISTINCT` alla SELECT                                             |
| `limit`, `offset` | Int        | Paginazione                                                                 |
| `orderBy`         | [Object]   | Ordinamento dei risultati                                                   |
| `groupBy`, `having` | [String] | Supporto ad aggregazioni e condizioni su aggregati                         |

#### Esempio di query GraphQL

```graphql
query {
  searchEntity(
    className: "http://dbpedia.org/ontology/Film"
    filters: [
      {
        path: [
          { property: "http://dbpedia.org/property/writer" },
          { property: "http://dbpedia.org/property/deathDate" }
        ]
      }
    ]
    optionalFilters: [
      { property: "http://dbpedia.org/ontology/budget" }
    ]
    selectFields: [
      "http://dbpedia.org/ontology/budget"
    ]
  )
}
```

#### SPARQL generato

```sparql
SELECT * WHERE {
  ?s a <http://dbpedia.org/ontology/Film> .
  ?s <http://dbpedia.org/property/writer> ?var_step_0_writer .
  ?var_step_0_writer <http://dbpedia.org/property/deathDate> ?var_step_1_deathDate .
  OPTIONAL { ?s <http://dbpedia.org/ontology/budget> ?var_budget . }
}
```

#### Risposta JSON attesa

```json
[
  {
    "film": "http://dbpedia.org/resource/Cabin_in_the_Sky_(film)",
    "budget": "679000.0"
  },
  ...
]
```

---

### `aggregateEntities`

Permette di eseguire aggregazioni SPARQL (`COUNT`, `SUM`, `AVG`, ...) su una proprietà, raggruppando per un’altra.

#### Parametri aggiornati

- `className` *(opzionale)* – Se presente, filtra le entità RDF da aggregare (es. solo entità di tipo `dbo:Film`)
- `groupBy` *(obbligatorio)* – URI della proprietà su cui eseguire il raggruppamento (es. `dbo:country`, `rdf:type`)
- `aggregation` *(obbligatorio)* – Oggetto che definisce il tipo di aggregazione:
  - `function`: Uno tra `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`
  - `on`: URI della proprietà da aggregare (oppure `"*"` per `COUNT(*)`)
  - `alias`: Nome della variabile risultante (es. `filmCount`, `totalBudget`)
- `having` *(opzionale)* – Condizioni da applicare al risultato aggregato (es. `SUM(?budget) > 1000000`)
- `orderBy` *(opzionale)* – Array di oggetti `{ property, order }` dove:
  - `property`: nome della variabile aggregata (es. `"filmCount"`)
  - `order`: `"ASC"` o `"DESC"`
- `limit`, `offset` *(opzionali)* – Controllano paginazione e offset nei risultati


#### Esempio di query GraphQL

```graphql
query {
  aggregateEntities(
    className: "http://dbpedia.org/ontology/Film"
    groupBy: "http://dbpedia.org/ontology/country"
    aggregation: {
      function: "COUNT"
      alias: "filmCount"
      on: "*"
    }
    orderBy: [{ property: "filmCount", order: "DESC" }]
    limit: 10
  )
}
```

#### SPARQL generato

```sparql
SELECT ?country (COUNT(*) AS ?filmCount) WHERE {
  ?s a <http://dbpedia.org/ontology/Film> .
  ?s <http://dbpedia.org/ontology/country> ?country .
}
GROUP BY ?country
ORDER BY DESC(?filmCount)
LIMIT 10
```

#### Risposta JSON attesa

```json
[
  {
    "country": "http://dbpedia.org/resource/India",
    "filmCount": "5915"
  },
  {
    "country": "http://dbpedia.org/resource/United_States",
    "filmCount": "1834"
  },
  {
    "country": "http://dbpedia.org/resource/Japan",
    "filmCount": "759"
  },
  ...
]
```

---

### `compareEntities`

Confronta entità RDF multiple (es. due film o due persone) che condividono uno o più percorsi/proprietà.
Permette di specificare condizioni tra le entità (es. disuguaglianze), confronti tra attori, registi o altre entità collegate.

#### Parametri

- `subjects`: array di entità, ognuna con 
  - `className`: URI della classe RDF
  - `alias`: nome personalizzato da usare nelle query
- `paths`: array di oggetti che descrivono i percorsi tra le entità
  - `from`: alias della risorsa di partenza
  - `path`: array di proprietà RDF (es. `["dbo:starring"]`)
  - `alias`: variabile SPARQL risultante (es. `actor1`)
- `filters`: array di condizioni tra le entità, ad esempio:
  - `?film1 != ?film2`
  - `?actor1 != ?actor2`
- `selectVars`: variabili da includere nella clausola `SELECT` (es. `["?film1", "?film2"]`)

#### Esempio di query GraphQL

```graphql
query {
  compareEntities(
    subjects: [
      { alias: "film1", className: "http://dbpedia.org/ontology/Film" }
      { alias: "film2", className: "http://dbpedia.org/ontology/Film" }
    ]
    paths: [
      { from: "film1", path: ["http://dbpedia.org/ontology/starring"], alias: "actor1" }
      { from: "film2", path: ["http://dbpedia.org/ontology/starring"], alias: "actor2" }
    ]
    filters: [
      "?film1 != ?film2",
      "?actor1 != ?actor2"
    ]
    selectVars: ["?film1", "?film2"]
  )
}
```

#### SPARQL generato

```sparql
SELECT ?film1 ?film2 WHERE {
  ?film1 a <http://dbpedia.org/ontology/Film> .
  ?film2 a <http://dbpedia.org/ontology/Film> .
  ?film1 <http://dbpedia.org/ontology/starring> ?actor1 .
  ?film2 <http://dbpedia.org/ontology/starring> ?actor2 .
  FILTER (?film1 != ?film2)
  FILTER (?actor1 != ?actor2)
}
```
#### Risposta JSON attesa

```json
[
  {
    "film1": "http://dbpedia.org/resource/Cab_Calloway's_Jitterbug_Party",
    "film2": "http://dbpedia.org/resource/Ca-bau-kan"
  },
  {
    "film1": "http://dbpedia.org/resource/Cab_Number_13",
    "film2": "http://dbpedia.org/resource/Ca-bau-kan"
  },
  ...
]

```

## Mapping GraphQL → SPARQL

Il sistema effettua una trasformazione automatica tra query GraphQL e SPARQL secondo regole predefinite.  
Di seguito una tabella di corrispondenza tra i costrutti GraphQL supportati e i costrutti SPARQL generati.

| Costrutto GraphQL             | Equivalente SPARQL                               |
|------------------------------|--------------------------------------------------|
| `className`                  | `?s a <classURI>`                                |
| `selectFields`               | `?s <property> ?var` per ciascuna proprietà      |
| `filters.path`               | Catena di triple con variabili intermedie       |
| `filters.value`              | `FILTER (?var = "valore")`                      |
| `optionalFilters`            | `OPTIONAL { ?s <property> ?var }`                |
| `notExistsFilters`           | `FILTER NOT EXISTS { ... }`                      |
| `existsFilters`              | `FILTER EXISTS { ... }`                          |
| `distinct: true`             | `SELECT DISTINCT`                                |
| `limit`, `offset`            | `LIMIT n`, `OFFSET m`                            |
| `orderBy`                    | `ORDER BY ASC(?var)` o `DESC(?var)`              |
| `groupBy`, `having`          | `GROUP BY`, `HAVING (...)`                       |
| `aggregation.function`       | `SUM`, `COUNT`, `AVG`, `MIN`, `MAX`              |
| `compareEntities.subjects`   | `?alias a <class>`                               |
| `compareEntities.sharedPaths`| Triple comuni su più entità                      |
| `compareEntities.filters`    | `FILTER (?var1 != ?var2)` tra entità             |

---

Tutti i nomi variabili (come `?var_step_0_writer`) vengono generati automaticamente a partire dall'URI della proprietà.

## Cambio RDF store a runtime

Graph2SPARQL consente di collegarsi a qualsiasi SPARQL endpoint dinamicamente, **senza modificare il codice Python**.

1. Apri il file `app/config/sparql_config.yaml`
2. Modifica tutto ciò che è necessario sotto `default:` , ad esempio per **Wikidata**:

```yaml
default:
  endpoint: "https://query.wikidata.org/sparql"
  prefixes:
    wd: "http://www.wikidata.org/entity/"
    wdt: "http://www.wikidata.org/prop/direct/"
    rdf: "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    rdfs: "http://www.w3.org/2000/01/rdf-schema#"
  query_syntax:
    select_format: |
      SELECT {modifiers}{select_vars} WHERE {{
        {main_pattern}
        {optional_patterns}
        {union_blocks}
        {filter_conditions}
      }}
    property_format: "{subject} <{property}> {object} ."
    optional_format: "OPTIONAL {{ {pattern} }}"
    filter_format: "FILTER ({condition})"
    union_format: "{{ {block} }}"
    group_by: "GROUP BY {group_by_fields}"
    having: "HAVING ({having_conditions})"
    order_by: "ORDER BY {order_by_conditions}"
    limit: "LIMIT {limit}"
    offset: "OFFSET {offset}"
  operator_map:
    "=": "{var} = {value}"
    "!=": "{var} != {value}"
    REGEX: "REGEX({var}, {value}, \"i\")"
    LANG_EQUALS: "LANG({var}) = {value}"
  options:
    language_filter: true
    default_language: "en"
    regex_filter: true
    main_patterns:
      - "?s wdt:P31 <{class_uri}> ."
```

3. Avvia il server specificando questo endpoint:

```bash
python server.py --endpoint "https://query.wikidata.org/sparql"
```

---

### Esempio di query GraphQL per Wikidata

```graphql
query {
  searchEntity(
    className: "http://www.wikidata.org/entity/Q5"  # Q5 = Person
    selectFields: [
      "http://www.wikidata.org/prop/direct/P569"    # birth date
    ]
    limit: 5
  )
}
```

### SPARQL generato

```sparql
SELECT ?s ?var_P569 WHERE {
  ?s wdt:P31 <http://www.wikidata.org/entity/Q5> . 
  ?s <http://www.wikidata.org/prop/direct/P569> ?var_P569 .
}
LIMIT 5
```



