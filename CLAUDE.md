# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Docker-based n8n workflow automation deployment with a custom HTML-to-PDF conversion microservice. The n8n instance runs alongside a Flask-based PDF conversion service, both orchestrated via Docker Compose.

## Architecture

### Services

1. **n8n Service**: The main workflow automation platform
   - Running on port 5678
   - Uses SQLite database with WAL mode enabled for better performance
   - Basic authentication configured via environment variables
   - Optimized for low-resource environments with concurrency limits
   - Connected to multiple networks including an external Supabase network

2. **HTML-to-PDF Converter Service**: Custom Flask microservice for PDF generation
   - Running on port 5000
   - Uses wkhtmltopdf with xvfb for headless PDF generation
   - Provides REST endpoint `/convert` accepting JSON with HTML content
   - Returns binary PDF data

### Network Configuration

- **n8n_network**: Internal bridge network for service communication
- **n8n_supabase_shared_app_network**: External network for Supabase integration

## Common Development Tasks

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start with rebuild (after code changes)
docker-compose up -d --build

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f n8n
docker-compose logs -f html_to_pdf_converter
```

### Testing PDF Converter

```bash
# Test the PDF converter directly
curl -X POST http://localhost:5000/convert \
  -H "Content-Type: application/json" \
  -d '{"html": "<h1>Test PDF</h1><p>This is a test.</p>"}' \
  --output test.pdf
```

### Environment Configuration

The `.env` file contains critical configuration:
- n8n authentication credentials (N8N_BASIC_AUTH_USER/PASSWORD)
- Webhook and application URLs for external access
- Timezone settings (TZ and GENERIC_TIMEZONE)

### Resource Management

The docker-compose.yml includes commented resource limits that can be enabled for production:
- CPU limits (example: 0.75 cores)
- Memory limits (example: 1GB)
- Configure via the `deploy.resources` section

## Working with the PDF Converter

### Key Implementation Details

- Uses tempfile for secure temporary file handling
- Implements comprehensive error handling and logging
- Cleans up temporary files in finally block
- UTF-8 encoding explicitly set for wkhtmltopdf
- Extensive debug output via print statements with sys.stdout.flush()

### Modifying the PDF Converter

When making changes to `html-to-pdf-service/app.py`:
1. The service logs extensively to stdout for debugging
2. All print statements are followed by `sys.stdout.flush()` for immediate output
3. Error responses include detailed information from wkhtmltopdf stderr/stdout
4. Temporary files are always cleaned up in the finally block

### Building and Deploying Changes

```bash
# Rebuild just the PDF converter
docker-compose build html_to_pdf_converter

# Restart the service
docker-compose restart html_to_pdf_converter
```

## Performance Optimization

The n8n configuration is optimized for low-resource environments:
- `EXECUTIONS_PROCESS=main`: Reduces process overhead
- `N8N_CONCURRENCY_PRODUCTION_LIMIT=1`: Limits concurrent workflow executions
- `DB_SQLITE_WAL_MODE=true`: Improves SQLite performance

## Data Persistence

n8n data is persisted to `/mnt/volume-nbg1-1/n8n/n8n_data` on the host, containing:
- SQLite database
- Binary data storage
- Configuration files
- SSH keys and Git configuration
- Event logs

## Security Considerations

- Basic authentication is enabled for n8n access
- PDF converter only accepts POST requests with JSON payloads
- Temporary files are created securely using mkstemp
- All services run in isolated Docker containers
- External network access is controlled via docker networks