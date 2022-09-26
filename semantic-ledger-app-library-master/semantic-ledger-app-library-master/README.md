# Semantic Ledger App Library

This is a library for use in the development of Semantic Ledger project-specific application APIs ("SL apps").

The library contains various modules and abstract classes for handling RDF and SL metadata, as well as wrapper functions for communicating with the domain-general Semantic Ledger API.

## Usage

- Make sure the sl_app folder is available for importing (for example by adding it to the PYTHONPATH)
- Make sure that Django files are mounted to the correct location where needed (e.g. the management commands in `scripts` might need to mount to `<project>/app/management/commands`)