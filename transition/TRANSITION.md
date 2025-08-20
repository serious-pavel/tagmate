# Tag Ordering Transition Guide

## Overview
We're implementing ordered tags functionality for TagGroup, which requires some structural changes.

Technically, you’ll only need to run a `migrate` command after updating the project code to the latest state. However, to avoid any risk of data loss, I recommend making a data backup before the transition.
## Transition Stages

###  Stage 1: Baseline
- **Tag**: v0.1-before-tg-tag-ordering
- **Action Recommended**: Database and Application data backup
- **Description**: Stable checkpoint before migration

```bash
checkout tags/v0.1-before-tg-tag-ordering
sh transition/backup.sh <postgres_container_id> <app_container_id> <db_user> <db_name> [tag/mark]
```

###  Stage 2: Cleanup
- **Tag**: v0.2-after-tg-tag-ordering
- **Action Required**: **MANDATORY MIGRATION**
- **Description**: Old implementation removed, new implementation only

```bash
checkout tags/v0.2-after-tg-tag-ordering
docker-compose run --rm app sh -c "python manage.py migrate"
```
