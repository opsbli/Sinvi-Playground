## ADDED Requirements

### Requirement: Sequential Stages Use Bound Agents

Sequential pipeline execution SHALL call the agent bound to each stage definition.

#### Scenario: Stage calls bound agent

- GIVEN a sequential pipeline definition has stage definitions with `agent_id`
- WHEN a pipeline run is executed
- THEN each stage SHALL call the agent referenced by its stage definition
- AND the stage artifact metadata SHALL include `agent_id` and `agent_name`

#### Scenario: Stage receives upstream artifacts

- GIVEN earlier stages have produced artifacts
- WHEN a later stage agent is called
- THEN the agent input SHALL include upstream artifact type, name, and content preview

#### Scenario: Missing stage agent blocks the run

- GIVEN a stage definition references an agent that does not exist
- WHEN that stage is executed
- THEN the stage SHALL become `blocked`
- AND the pipeline run SHALL become `blocked`
