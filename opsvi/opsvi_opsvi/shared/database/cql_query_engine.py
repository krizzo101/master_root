import json
from typing import Any


class CQLQueryEngine:
    def __init__(self, db):
        self.db = db  # Should be an arango database connection

    def run_cql(self, cql: dict[str, Any]) -> dict[str, Any]:
        results = {}
        for i, op in enumerate(cql.get("query", [])):
            if op["operation"] == "get_schema":
                results[op["collection"] + "_schema"] = self.get_schema(
                    op["collection"]
                )
            elif op["operation"] == "find":
                results[op["collection"] + "_find"] = self.find(op)
            elif op["operation"] == "aggregate":
                results[op["collection"] + "_aggregate"] = self.aggregate(op)
            elif op["operation"] == "join":
                results[op["from"] + "_join_" + op["to"]] = self.join(op)
        return results

    def get_schema(self, collection: str):
        # For demo, just return collection properties
        try:
            info = self.db.collection(collection).properties()
            return info
        except Exception as e:
            return {"error": str(e)}

    def find(self, op: dict[str, Any]):
        collection = op["collection"]
        filter_ = op.get("filter", {})
        limit = op.get("limit", 10)
        aql = f"FOR doc IN {collection} "
        if filter_:
            filters = [f"doc.{k} == @{k}" for k in filter_]
            aql += "FILTER " + " AND ".join(filters) + " "
        aql += f"LIMIT {limit} RETURN doc"
        try:
            cursor = self.db.aql.execute(aql, bind_vars=filter_)
            return list(cursor)
        except Exception as e:
            return {"error": str(e), "aql": aql}

    def aggregate(self, op: dict[str, Any]):
        collection = op["collection"]
        group_by = op.get("group_by", [])
        aql = f"FOR doc IN {collection} "
        if group_by:
            group_vars = ", ".join([f"{g} = doc.{g}" for g in group_by])
            aql += f"COLLECT {group_vars} WITH COUNT INTO count RETURN {{ {', '.join(group_by)}, count }}"
        else:
            aql += "COLLECT WITH COUNT INTO count RETURN { count }"
        try:
            cursor = self.db.aql.execute(aql)
            return list(cursor)
        except Exception as e:
            return {"error": str(e), "aql": aql}

    def join(self, op: dict[str, Any]):
        from_col = op["from"]
        to_col = op["to"]
        on = op["on"]  # {"from_field": "to_field"}
        from_field, to_field = list(on.items())[0]
        aql = f"FOR f IN {from_col} FOR t IN {to_col} FILTER f.{from_field} == t.{to_field} RETURN {{ f, t }}"
        try:
            cursor = self.db.aql.execute(aql)
            return list(cursor)
        except Exception as e:
            return {"error": str(e), "aql": aql}


# Demo usage (replace with real db connection in production)
if __name__ == "__main__":
    from arango import ArangoClient

    client = ArangoClient()
    db = client.db("_system", username="root", password="change_me")
    engine = CQLQueryEngine(db)
    cql = {
        "query": [
            {"collection": "rules", "operation": "get_schema"},
            {"collection": "rules", "operation": "find", "filter": {}, "limit": 2},
            {"collection": "metrics", "operation": "aggregate", "group_by": ["type"]},
            {
                "operation": "join",
                "from": "modules",
                "to": "tasks",
                "on": {"_key": "module_id"},
            },
        ]
    }
    print(json.dumps(engine.run_cql(cql), indent=2))
