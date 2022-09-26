# Changelog

## [Unreleased]

This is the first entry in this changelog for a repository that was for some time maintained without a changelog. Consequently, only recent changes are represented in this log entry.

### Added
- single_user_test_case class for basic get/post/list testcases where the user stays in control of their own assets.
- `rdf2jsontree` submodule which includes utility functions to convert RDF data (sub)graphs to "classic" JSON trees.
    - This module can now read SHACL shapes to determine whether RDF properties have singleton or multiple-allowed objects
- SL_View: `get_shape` function to retrieve the SHACL associated with a shape


### Changed
- Files and class names now comply with python naming conventions (PEP-8 style guide)

### Removed

<!-- Hyperlinks to the different versions -->