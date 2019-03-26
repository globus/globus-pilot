# JSON SCHEMA

This directory contains JSON Schemas used by this tool, following the spec
here: https://json-schema.org/

## Notes

There are two datacite specs:

* dc.json
* dc_strict.json

"dc_strict.json"refers to the actual datacite schema listed here:

https://github.com/datacite/schema/blob/master/source/json/kernel-4.2/datacite_4.2_schema.json

Currently, we are not minting DOIs and so have removed the "identifier" requirement,
which is the only change in `dc.json`