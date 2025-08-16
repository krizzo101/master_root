:param task_id => 'TASK-XYZ';

MATCH (:Task {id:$task_id})-[:DECIDED_BY]->(d:Decision)
OPTIONAL MATCH (d)-[:ASSERTS]->(c:Claim)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(e:Evidence)
OPTIONAL MATCH (d)-[:VERIFIED_BY]->(v:Verification)

WITH d, c, e, v
ORDER BY c.created_at ASC, e.created_at ASC, v.created_at ASC

WITH d, collect(DISTINCT c) AS claims, collect(DISTINCT e) AS evidence, collect(DISTINCT v) AS verifications

RETURN d, claims, evidence, verifications;
