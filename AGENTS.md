# Repository Guidelines

## Project Structure & Module Organization

Raio X is split into a FastAPI backend and a Next.js frontend. Backend code lives in `app/`: routes are in `app/routes.py`, SQLAlchemy entities in `app/models.py`, request/response types in `app/schemas.py`, and business metrics in `app/services.py`. Database initialization and seed data live in `scripts/bootstrap.py`.

The web application lives in `frontend/`. Next.js routes are under `frontend/app/`, shared components under `frontend/components/`, and API helpers/types under `frontend/lib/`. Keep visual tokens aligned with `design-system/MASTER.md`. Generated directories such as `.next/`, `node_modules/`, caches, and local environment files must not be committed.

## Build, Test, and Development Commands

- `docker compose up -d --build` builds PostgreSQL, the API, and the frontend.
- `docker compose exec api python -m scripts.bootstrap` creates tables and initial records.
- `uvicorn app.main:app --reload` runs the API locally on port 8000.
- `cd frontend && npm run dev` runs Next.js on port 3000.
- `cd frontend && npm run lint` checks React, accessibility, and TypeScript rules.
- `cd frontend && npm run build` verifies a production build.
- `python -m compileall app scripts` performs a backend syntax check.

## Coding Style & Naming Conventions

Use Python 3.12, four-space indentation, type hints, and Ruff formatting. Use TypeScript strict mode, two-space indentation, PascalCase React components, camelCase functions, and kebab-case route folders. Keep calculated indicators in `app/services.py`; never duplicate business formulas in the frontend. Use semantic CSS tokens rather than component-specific colors.

## Testing Guidelines

Add backend tests under `tests/` using names such as `test_attendance_rules.py`. Cover permission boundaries, hierarchy validation, sequential passwords, zero-denominator metrics, and audit records. Frontend changes must pass lint and production build; test important flows at 375px and desktop widths. Name UI tests by behavior, for example `entry-form.spec.ts`.

## Commit & Pull Request Guidelines

Use concise imperative subjects such as `Add attendance filters` or `Fix coordinator scope`. Keep commits focused. Pull requests should explain the behavior change, verification performed, configuration or schema impact, and linked issue. Include screenshots for visual changes and sample request/response payloads for API changes. Never commit secrets or production customer documents.
