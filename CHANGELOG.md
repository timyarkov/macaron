## v0.2.0 (2023-07-17)

### Feat

- resolve Maven properties in found POMs (#271)
- add support for cloning GitLab repositories (#316)
- multi build tool detection (#179)

### Fix

- check paths in an archive file before extracting (#366)
- fix CycloneDx Gradle automatic dependency resolver bug (#315)

## v0.1.1 (2023-06-14)

### Fix

- fix links as part of transition to oracle/macaron (#307)
- fixes the result summary for UNKNOWN check results (#299)

### Refactor

- separate provenance expectation from Datalog policies (#297)

## v0.1.0 (2023-06-05)

### Feat

- **release**: generate SLSA provenance for the Docker image (#265)
- add command-line flag for version (#262)
- add additional repo finding via parent POMs (#217)
- add repo finding via scm metadata in artefact poms (#155)
- run cue validator per analysis target  (#90)
- add python as a supported build tool (#67)
- support an existing SBOM as input (#105)
- add check output to database and implement souffle policy engine (#46)
- add dependency analyzer for Gradle (#57)

### Fix

- **release**: disable SLSA provenance for now (#277)
- do not skip rootProject in Gradle dependency resolution (#252)
- create the bin directory for syft (#245)
- add 'packages: read' permission to release workflow (#241)
- do not overwrite an existing check relationship when a check has no parent in the Registry (#238)
- upgrade requests to 2.31.0 to fix CVE-2023-32681 (#236)
- restore the runner if an uncaught exception happens in a check (#216)
- return error when defaults.ini provided by user does not exist (#208)
- fix undefined local variable in build_as_code check (#136)
- resolve the full name for a repo whose remote origin is a local path (#153)
- do not pull the latest when analyzing a target with local repo path (#125)
- do not use download script for Syft (#164)
- remove the topLevel packages permission (#160)
- initialize all DependencyInfo attributes (#139)
- check if build dir contains a valid build (#135)
- read configuration for recursion through bom file (#130)
- allow BOM component version and group be empty (#104)
- do not log check_module object to avoid info leakage (#96)

### Refactor

- run policy engine using macaron entrypoint (#192)
