# RFDS Driver Implementation Lifecycle

## Purpose

This document defines the mandatory implementation lifecycle for all
Robot Framework driver projects. It standardizes development into
**Phases** and **Gates** so that every delivery is small enough to
review, test, and package while remaining production quality.

------------------------------------------------------------------------

# Project Structure

A project is divided into sequential **Phases**.

Each Phase is divided into **five Gates**.

    Phase N
    │
    ├── Gate 1 – Architecture & Skeleton
    ├── Gate 2 – Core Implementation
    ├── Gate 3 – Extended Features
    ├── Gate 4 – Tests & Documentation
    └── Gate 5 – Review & Release

A gate must be completed and approved before the next gate begins.

------------------------------------------------------------------------

# Gate 1 -- Architecture & Skeleton

## Objective

Create or extend the architecture required for the current phase.

### Deliverables

-   Folder structure
-   Interfaces
-   Base classes
-   Data models
-   Configuration updates
-   Architecture documentation
-   Buildable package

### Acceptance Criteria

-   Package builds successfully
-   Coding standards followed
-   Architecture documented
-   No Critical review findings

------------------------------------------------------------------------

# Gate 2 -- Core Implementation

## Objective

Implement the primary functionality.

### Deliverables

-   Core Python implementation
-   Robot Framework keywords
-   Public API
-   Error handling
-   Initial examples

### Acceptance Criteria

-   Main functionality operational
-   Robot keywords verified
-   Unit tests for implemented features

------------------------------------------------------------------------

# Gate 3 -- Extended Features

## Objective

Complete all remaining functionality defined for the phase.

### Deliverables

-   Advanced features
-   Edge-case handling
-   Performance improvements
-   Configuration enhancements
-   AI metadata updates

### Acceptance Criteria

-   Feature complete for the phase
-   API remains backward compatible
-   Documentation updated

------------------------------------------------------------------------

# Gate 4 -- Tests & Documentation

## Objective

Validate and document the implementation.

### Deliverables

-   Unit tests
-   Integration tests
-   Robot Framework examples
-   API documentation
-   User guide
-   Developer guide
-   Updated README

### Acceptance Criteria

-   Target code coverage achieved
-   All tests passing
-   Examples verified on supported hardware where applicable

------------------------------------------------------------------------

# Gate 5 -- Review & Release

## Objective

Finalize the phase for release.

### Deliverables

-   Code review
-   Architecture review
-   Robot API review
-   Documentation review
-   Performance review
-   Bug fixes
-   Changelog
-   Release notes
-   ZIP package

### Acceptance Criteria

-   No Critical issues
-   Major issues resolved or documented
-   Phase approved for continuation

------------------------------------------------------------------------

# Phase Completion

A phase is complete only when all five gates have been approved.

Each phase must produce:

-   Updated documentation
-   Updated AI Driver Contract
-   Updated examples
-   Updated tests
-   Updated history/
-   Updated review/
-   Production-ready ZIP package

------------------------------------------------------------------------

# Versioning

Each gate produces a versioned release.

    Phase 1
    v26.01.01 Gate 1
    v26.01.02 Gate 2
    v26.01.03 Gate 3
    v26.01.04 Gate 4
    v26.01.05 Gate 5

    Phase 2
    v26.02.01
    v26.02.02
    v26.02.03
    v26.02.04
    v26.02.05

------------------------------------------------------------------------

# Mandatory Reviews

Every Gate shall include:

1.  Functional review
2.  Architecture review
3.  Robot Framework API review
4.  Documentation review
5.  Code quality review

Every Phase shall additionally include:

-   Regression review
-   Performance review
-   Release readiness review

------------------------------------------------------------------------

# Benefits

This methodology provides:

-   Small, reviewable implementation increments
-   Continuous testing
-   Continuous documentation
-   Predictable releases
-   Easier AI-assisted implementation
-   Reduced integration risk
-   Consistent lifecycle across all Robot Framework drivers
