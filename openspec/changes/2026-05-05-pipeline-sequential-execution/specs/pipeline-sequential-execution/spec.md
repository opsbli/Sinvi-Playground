## ADDED Requirements

### Requirement: Sequential pipeline runs complete ordered AI Coding stages
The system SHALL execute `designer`, `reviewer`, `coder`, and `validator` stages in stage order for a pipeline run.

#### Scenario: Run all stages successfully
- GIVEN a pipeline run has pending stage runs for `designer`, `reviewer`, `coder`, and `validator`
- WHEN the sequential runner executes with successful stage handlers
- THEN each stage run is marked `completed`
- AND the pipeline run is marked `done`
- AND each stage output is persisted as an artifact

### Requirement: Stage failures block the pipeline run
The system SHALL preserve stage errors and stop execution when a stage is blocked.

#### Scenario: Stage handler fails
- GIVEN a pipeline run is executing a stage
- WHEN the stage handler raises an error or returns blocked
- THEN that stage run is marked `blocked`
- AND the pipeline run is marked `blocked`
- AND no later stage is executed

### Requirement: Validator failures create coder retry attempts
The system SHALL route failed validation back to coder by creating a new coder attempt.

#### Scenario: Validator rejects implementation
- GIVEN designer, reviewer, coder, and validator stages have executed
- WHEN validator returns `passed` as false
- THEN validator stage run is marked `failed`
- AND the pipeline run remains active with current stage set to coder
- AND a new pending coder stage run is created with the next attempt number

### Requirement: Pipeline execution trace is persisted
The system SHALL persist trace events for stage lifecycle and retry decisions.

#### Scenario: Stage trace events are recorded
- WHEN a sequential pipeline run executes stages
- THEN trace artifacts record stage start, stage completion, blocked, and retry events
