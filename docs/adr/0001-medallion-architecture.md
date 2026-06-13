# ADR-0001: Medallion Architecture (Bronze/Silver/Gold)

**Status**: Accepted
**Date**: 2026-02-15
**Authors**: Data Engineering Team

> **Note:** Implementation details (tooling, storage) have evolved since this ADR was written. See [docs/architecture.md](docs/architecture.md) for the current design. References to ADR-0002, ADR-0003, and ADR-0004 are placeholders for decisions that were planned but not written.

## Context

DEX needs a scalable, standardized data architecture that works across all projects (CareerDEX, Weather, etc.). The data pipeline needs to handle:

- Raw data ingestion from multiple sources
- Data transformation and quality validation
- Feature engineering for ML models
- Analytics-ready data consumption

Multiple projects will be built on the DEX platform, each with different data sources and transformations. We need a consistent, reusable pattern.

## Decision

Implement the **Medallion Architecture** (Bronze → Silver → Gold layers) as the standard data architecture for all DEX projects.

### Architecture Layers

1. **Bronze Layer (Raw Data)**

   - Stores raw data as-is from sources
   - No transformation applied
   - Schema validation only
   - High volume, immutable records
   - Storage: Parquet (local) + BigQuery (`*_bronze` datasets)

1. **Silver Layer (Processed & Normalized)**

   - Data parsed and normalized
   - Quality validated
   - Deduplication applied
   - Schema consistent across sources
   - Sensitive data masked/redacted
   - Storage: BigQuery (`*_silver` datasets) + embeddings cache (Redis)

1. **Gold Layer (Aggregated & Analytics)**

   - Business-ready features
   - Pre-computed aggregations
   - ML model predictions
   - Denormalized for performance
   - Storage: BigQuery (`*_gold` datasets)

### Implementation

For each project (CareerDEX, Weather, etc.):

```
<project>_bronze   → Raw data from APIs/sources
<project>_silver   → Parsed, validated data
<project>_gold     → Features, aggregations, ML outputs
```

Local development:

```
~/data/<project>/bronze/
~/data/<project>/silver/
~/data/<project>/gold/
```

## Considered Alternatives

### 1. Single Large Table

- Pros: Simpler schema
- Cons: Difficult to scale, hard to debug data quality issues

### 2. Flat File Structure

- Pros: Works for small projects
- Cons: No schema governance, difficult to track lineage

### 3. Data Vault 2.0

- Pros: Highly normalized, strong audit trail
- Cons: Over-engineered for current needs, complex

## Consequences

### Positive

- **Scalability**: Easy to add new projects following same pattern
- **Debugging**: Issues isolated to specific layer
- **Quality**: Explicit data quality checks at Silver layer
- **Reusability**: Silver/Gold layers shareable across teams
- **Lineage**: Clear data flow and dependencies
- **Performance**: Gold layer optimized for queries

### Negative

- **Storage**: Triple storage for each dataset (3x costs)
- **Complexity**: More orchestration needed
- **Late binding**: Features computed in Gold, not in source

### Neutral

- Requires discipline to not skip layers
- Needs monitoring to catch quality issues

## Implementation Notes

### Phase 1 (v0.2.0)

- Define schemas for each layer
- Implement validation framework
- Create local Parquet directories
- Set up BigQuery datasets

### Phase 2 (CareerDEX v0.5.0)

- Implement Bronze ingest (Airflow orchestration)
- Implement Silver transformation (parsing, validation)
- Populate Gold with features/predictions

### Migration Path

If moving from existing flat structure:

1. Map existing tables to layers
1. Create Parquet exports at each layer
1. Validate data transformations
1. Gradually migrate pipelines

## Tooling

- **Storage**: BigQuery (cloud), Parquet (local)
- **Transformations**: dbt (SQL) or Spark (Python)
- **Orchestration**: Apache Airflow
- **Quality Validation**: Great Expectations + Pydantic
- **Lineage Tracking**: dbt lineage + custom metadata

## Related Decisions

- **ADR-0002**: Using dbt for Silver/Gold transformations
- **ADR-0003**: Data quality framework
- **ADR-0004**: Feature store strategy

## References

- [Databricks Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- Issue: #35 (Define storage layers)
- PR: #XXX (Schema definitions)

## Monitoring & Governance

**Golden Rules**:

1. ✅ Never skip a layer
1. ✅ Always validate schema at layer boundaries
1. ✅ Document transformations between layers
1. ✅ Track data lineage
1. ✅ Monitor quality metrics

**Metrics to Track**:

- Row counts at each layer
- Quality validation pass rate
- Transformation latency
- Storage usage by layer

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-15 | Data Team | Initial acceptance |
