# Tag Ordering Transition Guide

## Overview
We're implementing ordered tags functionality for TagGroup in 3 transition stages.

## Transition Stages

###  Stage 1: Baseline
- **Tag**: v0.1-before-tg-tag-ordering
- **Action Recommended**: Database and Application data backup
- **Description**: Stable checkpoint before migration

###  Stage 2: Dual Implementation
- **Tag**: v0.2-transition-tg-tag-ordering
- **Action Required**: in strict order **MANDATORY MIGRATION** first, **FULFILL NEW RELATIONSHIPS** then
- **Description**: New functionality added, old functionality preserved for compatibility

### Stage 3: Cleanup
- **Tag**: v0.3-after-tg-tag-ordering
- **Action Required**: **MANDATORY MIGRATION**
- **Description**: Old implementation removed, new implementation only
