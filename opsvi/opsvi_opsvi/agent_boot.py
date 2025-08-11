import os

from arango import ArangoClient

ARANGO_URL = os.getenv("ARANGO_URL", "http://127.0.0.1:8550")
ARANGO_PASS = os.getenv("ARANGO_PASS", "change_me")
client = ArangoClient(hosts=ARANGO_URL)
sys_db = client.db("_system", username="root", password=ARANGO_PASS)
research = sys_db.collection("research_docs")


def semantic_search(query_vec, limit=3):
    aql = '\n    FOR doc IN research_view\n      SEARCH ANALYZER(SIMILARITY(doc.vector,@vec) > 0.8,"cosine")\n      LIMIT @limit\n      RETURN {title:doc.title, url:doc.source_url}\n    '
    cursor = sys_db.aql.execute(aql, bind_vars={"vec": query_vec, "limit": limit})
    return [d for d in cursor]
