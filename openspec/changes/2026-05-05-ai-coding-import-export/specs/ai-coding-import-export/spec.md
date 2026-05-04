## ADDED Requirements

### Requirement: Legacy AI Coding story bundles can be imported into pipeline runs
The system SHALL import one legacy `worker/stories/<story-id>` folder and optional shared PRD into a pipeline run.

#### Scenario: Import a story folder
- GIVEN a legacy story folder contains `story.md` and `status.json`
- WHEN the importer runs for that story folder
- THEN the system creates a pipeline run with the story content in `input_payload`
- AND the system persists `story` and `prd` artifacts when source files exist
- AND the system persists known stage output files as pipeline artifacts

### Requirement: Pipeline runs can be exported as legacy story bundles
The system SHALL export a pipeline run into a file structure compatible with the legacy worker story bundle.

#### Scenario: Export pipeline run
- GIVEN a pipeline run contains story, PRD, and stage output artifacts
- WHEN the exporter writes a legacy bundle
- THEN it writes `story.md`, `status.json`, known stage output files, and `shared/prd.md`

### Requirement: Import/export results are repeatable
The system SHALL produce stable import/export outputs for the same source data.

#### Scenario: Re-export the same run
- GIVEN a pipeline run has already been exported
- WHEN the exporter runs again to the same output directory
- THEN the same expected files are overwritten with current pipeline content
