
/* Decision / Claim / Evidence / Verification migration */

// Constraints
CREATE CONSTRAINT claim_id_unique     IF NOT EXISTS FOR (c:Claim)    REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT evidence_id_unique  IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT verify_id_unique    IF NOT EXISTS FOR (v:Verification) REQUIRE v.id IS UNIQUE;

CREATE INDEX claim_hash_index     IF NOT EXISTS FOR (c:Claim)    ON (c.hash);
CREATE INDEX evidence_sha_index   IF NOT EXISTS FOR (e:Evidence) ON (e.sha256);
CREATE INDEX evidence_time_index  IF NOT EXISTS FOR (e:Evidence) ON (e.retrieved_at);

// Example write procedures (adapt to your driver):
// MATCH (t:Task {id:$task_id})
// MERGE (d:Decision {id:$decision_id})
//   ON CREATE SET d += $props
// MERGE (t)-[:DECIDED_BY]->(d);

// Claims & Evidence
// MERGE (c:Claim {id:$claim_id}) ON CREATE SET c.text=$text, c.hash=$hash
// MERGE (d:Decision {id:$decision_id})
// MERGE (d)-[:ASSERTS]->(c);

// UNWIND $evidence_list AS ev
// MERGE (e:Evidence {id:ev.id}) ON CREATE SET e += ev
// MERGE (c)-[:SUPPORTED_BY]->(e);

// Verification
// MERGE (v:Verification {id:$ver_id}) ON CREATE SET v += $props
// MERGE (d:Decision {id:$decision_id})
// MERGE (d)-[:VERIFIED_BY]->(v);
