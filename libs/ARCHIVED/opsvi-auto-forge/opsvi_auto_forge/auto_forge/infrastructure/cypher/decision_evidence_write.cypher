/* Parameters: change before running */
:param task_id => 'task-evidence-test';
:param decision_id => 'decision-evidence-test';
:param claim_id => 'claim-evidence-test';
:param claim_text => 'Agent asserts implementation satisfies spec X with Y tests passing.';
:param evidence => [
  {id:'ev-test-1', source_type:'file', uri:'file://repo/path/file.py', sha256:'a76c3f94601743afc3a11c09ccb75f56839c1bc422aaad314d40b2f29372693d', score:0.92, span_start:10, span_end:120, retrieved_at:datetime()},
  {id:'ev-test-2', source_type:'web', uri:'https://example.com/doc', sha256:'b87d4f05712850bfd4b22d20ddb86f6794ac2d235bbad425e41b3f30482737e', score:0.85, span_start:null, span_end:null, retrieved_at:datetime()}
];

MERGE (t:Task {id:$task_id})
MERGE (d:Decision {id:$decision_id})
  ON CREATE SET d.created_at = datetime()
MERGE (t)-[:DECIDED_BY]->(d)

MERGE (c:Claim {id:$claim_id})
  ON CREATE SET c.text = $claim_text, c.created_at = datetime()

MERGE (d)-[:ASSERTS]->(c)

UNWIND $evidence AS ev
MERGE (e:Evidence {id:ev.id})
  ON CREATE SET e += ev
MERGE (c)-[:SUPPORTED_BY]->(e);

RETURN d.id AS decision, c.id AS claim, size($evidence) AS evidence_count;
