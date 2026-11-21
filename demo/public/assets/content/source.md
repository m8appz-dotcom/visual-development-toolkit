# Architecture

Content Engine v2 is a clean-room rebuild of the original content pipeline.

## Pipeline

Source Registry → Evidence → Story angles → Script → Validation → Human approval → Rendering

Model output is validated before it is written to the database. Public examples use allowlisted evidence. Human approval remains a separate decision.

This excerpt summarizes the public architecture for the interactive English example. It is not a record of a completed publication.
