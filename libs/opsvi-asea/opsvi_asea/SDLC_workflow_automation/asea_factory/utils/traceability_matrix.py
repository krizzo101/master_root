import yaml
from asea_factory.schemas import TraceabilityMatrix


def generate_traceability_matrix(requirements, architecture, code, tests, docs):
    mapping = {}
    for req in requirements:
        req_id = req["id"] if isinstance(req, dict) else req.id
        mapping[req_id] = {
            "architecture": [architecture["id"]] if architecture else [],
            "code": [c["id"] for c in code if req_id in c.get("requirements", [])],
            "tests": [t["id"] for t in tests if req_id in t.get("requirements", [])],
            "docs": [d["id"] for d in docs if req_id in d.get("requirements", [])],
        }
    matrix = TraceabilityMatrix(
        requirements=[r["id"] if isinstance(r, dict) else r.id for r in requirements],
        architecture=[architecture["id"]] if architecture else [],
        code=[c["id"] for c in code],
        tests=[t["id"] for t in tests],
        docs=[d["id"] for d in docs],
        mapping=mapping,
    )
    with open("docs1/Traceability_Matrix.md", "w") as f:
        f.write(matrix.model_dump_json(indent=2))
    with open("docs1/Traceability_Matrix.yaml", "w") as f:
        yaml.safe_dump(matrix.model_dump(), f)
    return matrix
