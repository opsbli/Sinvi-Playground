## ADDED Requirements

### Requirement: AI Coding agents are imported with stable role metadata
The system SHALL import the `designer`, `reviewer`, `coder`, and `validator` prompts from `ai_coding/worker/agents/*.md` into the agent store.

#### Scenario: Import AI Coding role agents
- WHEN the AI Coding agent importer runs with a directory containing all four role prompt files
- THEN the system creates one agent for each role
- AND the system records source metadata with `pipeline_family` set to `ai_coding`
- AND the metadata records the role, source provider, source path, and source hash for each imported agent

### Requirement: AI Coding agent import is idempotent
The system SHALL upsert imported AI Coding agents by `pipeline_family` and `role`.

#### Scenario: Re-run AI Coding agent import
- GIVEN the AI Coding agent importer has already imported all four role agents
- WHEN the importer runs again against the same prompt directory
- THEN no duplicate agents are created
- AND the importer returns the same agent ids for each role

### Requirement: Imported AI Coding agents can be referenced by pipeline stages
The system SHALL make imported AI Coding agent ids usable as pipeline stage `agent_id` values.

#### Scenario: Create pipeline definition with imported designer agent
- GIVEN the AI Coding designer agent has been imported
- WHEN a pipeline definition creates a stage with the imported designer agent id
- THEN the pipeline stage persists that agent id for later execution
