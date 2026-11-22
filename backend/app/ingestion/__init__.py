"""Data ingestion: connectors fetch raw input, schemas validate it, jobs apply business rules.

Jobs never overwrite existing records with different values: differences are recorded as
conflicts on the ingestion run for a human to resolve.
"""
