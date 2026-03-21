# Personal CRM

A relationship management system that automatically discovers contacts from your email and calendar, tracks interactions, and provides intelligent relationship insights.

## Architecture

```
crm/
├── config/           # Configuration files
├── database/         # Database schema and models
├── pipelines/        # Data ingestion pipelines
├── nlp/             # Natural language interface
├── intelligence/     # Relationship scoring and insights
├── cron/            # Scheduled jobs
├── email_drafts/    # Email composition system
└── api/             # API and CLI interface
```

## Quick Start

1. Configure your integrations in `config/settings.yaml`
2. Initialize the database: `python -m crm.database.init`
3. Run initial sync: `python -m crm.pipelines.discovery --full-sync`
4. Start the API: `python -m crm.api.server`

## Database Schema

See `database/schema.sql` for full schema.

## Configuration

Copy `config/settings.yaml.example` to `config/settings.yaml` and fill in your credentials.
