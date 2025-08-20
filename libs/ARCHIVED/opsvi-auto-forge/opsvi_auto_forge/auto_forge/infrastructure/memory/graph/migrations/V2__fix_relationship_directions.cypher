-- V2__fix_relationship_directions.cypher
-- Migration to fix relationship direction inconsistencies
-- Changes PART_OF relationships to proper HAS_TASK relationships

-- Step 1: Check for existing PART_OF relationships
MATCH (t:Task)-[r:PART_OF]->(run:Run)
RETURN count(r) as part_of_relationships;

-- Step 2: Migrate PART_OF relationships to HAS_TASK
MATCH (t:Task)-[r:PART_OF]->(run:Run)
CREATE (run)-[:HAS_TASK]->(t)
DELETE r
RETURN count(*) as migrated_relationships;

-- Step 3: Check for any remaining PART_OF relationships (should be 0)
MATCH (t:Task)-[r:PART_OF]->(run:Run)
RETURN count(r) as remaining_part_of_relationships;

-- Step 4: Fix any GENERATES relationships to PRODUCES
MATCH (t:Task)-[r:GENERATES]->(a:Artifact)
CREATE (t)-[:PRODUCES]->(a)
DELETE r
RETURN count(*) as migrated_generates_relationships;

-- Step 5: Fix any PART_OF_RUN relationships to HAS_TASK
MATCH (t:Task)-[r:PART_OF_RUN]->(run:Run)
CREATE (run)-[:HAS_TASK]->(t)
DELETE r
RETURN count(*) as migrated_part_of_run_relationships;

-- Step 6: Verify all relationships are now consistent
MATCH (r:Run)-[:HAS_TASK]->(t:Task)
RETURN count(*) as has_task_relationships;

-- Step 7: Clean up any orphaned relationships
MATCH ()-[r:PART_OF]-() DELETE r;
MATCH ()-[r:GENERATES]-() DELETE r;
MATCH ()-[r:PART_OF_RUN]-() DELETE r;

-- Step 8: Create a summary report
RETURN {
    message: 'Relationship direction migration completed',
    has_task_relationships: count(MATCH (r:Run)-[:HAS_TASK]->(t:Task) RETURN 1),
    produces_relationships: count(MATCH (t:Task)-[:PRODUCES]->(a:Artifact) RETURN 1),
    has_result_relationships: count(MATCH (t:Task)-[:HAS_RESULT]->(res:Result) RETURN 1),
    has_critique_relationships: count(MATCH (t:Task)-[:HAS_CRITIQUE]->(c:Critique) RETURN 1),
    has_decision_relationships: count(MATCH (t:Task)-[:HAS_DECISION]->(d:Decision) RETURN 1)
} as migration_summary;
