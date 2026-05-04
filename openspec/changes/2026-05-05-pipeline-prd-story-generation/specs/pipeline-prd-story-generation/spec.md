## ADDED Requirements

### Requirement: Product briefs can be persisted as PRD artifacts
The system SHALL generate and persist a PRD artifact from a product brief.

#### Scenario: Generate PRD from brief
- WHEN a caller runs PRD story generation with a product brief
- THEN the system creates a pipeline run
- AND the system writes one `prd` artifact containing the original brief and PRD sections
- AND the PRD artifact metadata records the source brief

### Requirement: PRD artifacts can be split into Story artifacts
The system SHALL split a PRD artifact into one or more Story artifacts.

#### Scenario: Split PRD into stories
- GIVEN a PRD artifact exists for a pipeline run
- WHEN the system splits the PRD
- THEN the system writes one or more `story` artifacts for the same run
- AND each Story artifact has stable `story_id`, `title`, and `source_prd_artifact_id` metadata

### Requirement: Story artifacts can seed sequential pipeline runs
The system SHALL allow a Story artifact payload to be used as the `input_payload` for a pipeline run.

#### Scenario: Create story execution run from Story artifact
- GIVEN a Story artifact exists
- WHEN a caller creates a pipeline run with the Story artifact id and content in `input_payload`
- THEN the created run preserves the Story artifact input payload
