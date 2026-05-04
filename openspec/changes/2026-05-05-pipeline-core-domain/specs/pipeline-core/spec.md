## ADDED Requirements

### Requirement: Pipeline definitions are persisted with ordered stages
The system SHALL allow clients to create and read pipeline definitions with ordered stage definitions.

#### Scenario: Create a pipeline definition
- WHEN a client submits a pipeline definition with `name`, `kind`, optional `description`, and one or more stages
- THEN the system persists the definition and every stage
- AND each stage has a stable id, `stage_order`, `role`, `agent_id`, and default `retry_limit` of 1 when omitted
- AND reading the definition returns stages ordered by `stage_order`

#### Scenario: Reject duplicate stage order
- WHEN a client submits a pipeline definition with duplicate `stage_order` values
- THEN the system rejects the request as a client validation error
- AND the system does not persist the invalid definition

#### Scenario: Reject orphan stage definitions
- WHEN a pipeline stage definition references a missing pipeline definition
- THEN the database rejects the row with a foreign key error

### Requirement: Pipeline runs initialize pending stage runs
The system SHALL allow clients to create a pipeline run for an existing pipeline definition without executing any stages.

#### Scenario: Create a pipeline run
- GIVEN a pipeline definition with ordered stages exists
- WHEN a client creates a run with `title` and `input_payload`
- THEN the system persists the run with status `pending`
- AND the run `current_stage_id` references the first stage definition
- AND the system creates one pending stage run for each stage definition
