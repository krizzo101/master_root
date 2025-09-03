# SQL System Discovery Questions

Please provide detailed information about the SQL system you designed that integrates chat logs and .proj-intel data:

## 1. Database Technology & Infrastructure

### Core Technology
- What database system are you using? (SQLite, PostgreSQL, MySQL, etc.)
- What is the database file path or connection string?
- Are there any extensions or plugins enabled? (e.g., TimescaleDB, pgvector, FTS5 for SQLite)
- What's the current database size and row count?

### Performance & Scalability
- How many records are currently stored?
- What's the ingestion rate (records per second/minute)?
- Are there any performance bottlenecks you've identified?
- What indexing strategy are you using?

## 2. Schema Design

### Tables Structure
Please provide the complete schema including:
- All table names and their purposes
- Column definitions with data types
- Primary keys and foreign keys
- Indexes (including composite indexes)
- Any views or materialized views
- Triggers or stored procedures

### Data Model for Integration
- How are chat logs structured in the database?
- How is .proj-intel data stored?
  - Is it normalized or stored as JSON/BLOB?
  - How do you handle the JSONL format?
  - How do you store file analysis, symbols, dependencies?
- How do you link/relate chat logs to code intelligence data?
- What's the relationship model between different data sources?

## 3. .proj-intel Integration Details

### Ingestion Process
- How do you parse and ingest .proj-intel JSONL files?
- Do you store the raw JSONL or transform it?
- How do you handle updates when .proj-intel is regenerated?
- Is ingestion real-time, batch, or on-demand?

### Data Mapping
- How do you map .proj-intel concepts to database tables?
  - Files and their metadata
  - Functions, classes, symbols
  - Dependencies and imports
  - Complexity metrics
  - Test coverage data
- Do you maintain the byte-offset index information?
- How do you handle the reverse index?

## 4. Chat Log Integration

### Message Storage
- How are conversations/sessions structured?
- How do you store tool use and results?
- How do you handle message threading and branches?
- What metadata do you capture (timestamps, costs, tokens, etc.)?

### Correlation with Code
- How do you identify when chat messages reference code?
- Do you extract file paths, function names from chat content?
- How do you link chat discussions to specific code elements?

## 5. Query Patterns & Access

### Common Queries
- What are the most common query patterns?
- How do you search across both chat and code data?
- Do you support full-text search? How?
- Can you do semantic/similarity search?

### API/Access Layer
- Is there an API layer on top of the database?
- What ORMs or query builders are you using?
- How do other systems access this data?

## 6. Special Features

### Temporal Aspects
- How do you handle time-series data?
- Can you query "state at a point in time"?
- How do you track changes over time?

### Relationships & Correlations
- How do you model relationships between entities?
- Can you traverse relationships (e.g., "find all chats about functions that call X")?
- Do you store computed correlations?

### Caching & Optimization
- Is there a caching layer?
- What gets cached and for how long?
- How do you handle cache invalidation?

## 7. Migration & Compatibility

### Current Limitations
- What limitations have you encountered with the current design?
- What features are difficult or impossible to implement?
- Where are the performance bottlenecks?

### Data Export
- Can you export the schema as SQL DDL?
- Can you provide sample data (anonymized if needed)?
- What format would be best for data migration?

### Future Considerations
- What changes would you make if redesigning?
- What features do you wish the database supported?
- Are there specific PostgreSQL features that would help?

## 8. Code & Configuration

### Implementation Files
- Where is the database initialization code?
- Where are the model/schema definitions?
- Where is the ingestion pipeline code?
- Where are the query interfaces?

### Configuration
- What environment variables or config files control the database?
- How do you handle database migrations/schema updates?
- Is there a backup strategy?

## Example Output Request

Could you provide:
1. The complete SQL schema (CREATE TABLE statements)
2. A few example records from each main table
3. An example of a complex query joining chat and code data
4. The file paths to the implementation code

## Additional Context

We're considering whether to:
- Continue with your current SQL implementation
- Migrate to PostgreSQL with TimescaleDB and pgvector
- Build on top of your existing system

Your detailed answers will help us make an informed decision about whether migration is necessary or if we can extend your current implementation.

---

Please be as specific and technical as possible. Include actual SQL statements, code snippets, and file paths where relevant.
