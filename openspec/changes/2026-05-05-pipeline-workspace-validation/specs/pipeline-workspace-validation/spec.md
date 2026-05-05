## ADDED Requirements

### Requirement: Pipeline Workspace Materialization

Coder stage SHALL be able to materialize explicit file blocks into a run-scoped workspace.

#### Scenario: Coder writes declared files

- GIVEN coder agent output contains a `pipeline-file` fenced block with a relative path
- WHEN coder stage completes
- THEN the file SHALL be written under the run workspace
- AND a `workspace_manifest` artifact SHALL list the generated file

#### Scenario: Coder cannot write outside workspace

- GIVEN coder agent output contains an absolute path or `..` path
- WHEN coder stage completes
- THEN the stage SHALL become `blocked`
- AND no file SHALL be written outside the run workspace

### Requirement: Pipeline Validation Commands

Validator stage SHALL execute configured validation commands in the run workspace.

#### Scenario: Validation command passes

- GIVEN run input includes `validation_commands` as argv arrays
- WHEN validator stage executes
- THEN each command SHALL run with cwd set to the run workspace
- AND validation artifacts SHALL record stdout, stderr, and exit code
- AND validator output SHALL include `passed=true`

#### Scenario: Validation command fails

- GIVEN a validation command exits non-zero
- WHEN validator stage executes
- THEN validation artifacts SHALL record the non-zero exit code
- AND validator output SHALL include `passed=false`
