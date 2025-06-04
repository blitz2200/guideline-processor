# Guideline Processor API

A minimal backend API that processes guideline documents using a two-step GPT chain (summarize → generate checklist) with async job processing.

## Architecture

**Stack**: Django + DRF + Celery + Redis + PostgreSQL + OpenAI GPT

**Design Choices**:
- **Async Processing**: Jobs queued with Celery for sub-200ms response times
- **Two-Step GPT Chain**: First summarizes guidelines, then generates actionable checklists
- **FIFO Queue**: Redis-backed Celery ensures proper job ordering
- **Database**: PostgreSQL for production, SQLite for development
- **API Documentation**: Auto-generated OpenAPI spec with Swagger UI

## Quick Start

1. **Setup environment**:
   ```bash
   cp .env.example .env
   # Add your OpenAI API key to .env
   ```

2. **One-command bootstrap**:
   ```bash
   docker compose up --build
   ```

3. **Run tests**:
   ```bash
   docker compose exec web python manage.py test
   docker compose exec web coverage run --source='.' manage.py test
   docker compose exec web coverage report
   ```

## API Endpoints

- `POST /jobs/` - Submit guideline for processing (returns event_id in <200ms)
- `GET /jobs/{event_id}/` - Check job status and results
- `GET /docs/` - Swagger UI documentation
- `GET /schema/` - OpenAPI schema

## Example Usage

```bash
# Submit job
curl -X POST http://localhost:8000/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"guideline_text": "Safety guidelines for laboratory work..."}'

# Check status
curl http://localhost:8000/jobs/{event_id}/
```

## AI Tools Used

- **Claude/GPT**: Generated project structure, Django models, serializers, and test cases
- **AI-assisted**: API design, Celery task implementation, Docker configuration
- **Human refinement**: OpenAI integration, error handling, test coverage optimization

The AI tools significantly accelerated development by providing boilerplate code and architectural patterns, allowing focus on business logic and integration details.