# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SwanLab-Dashboard (SwanBoard) is a training visualization service for machine learning experiments. It provides a FastAPI backend with a Vue.js frontend for visualizing ML training metrics and experiment data. The system uses MySQL for data persistence and is designed to be integrated into the SwanLab framework via `swanlab watch`.

**Key separation of concerns:**
- SwanBoard only provides visualization services for training data; it does not participate in the training process itself
- SwanBoard is imported as a dependency into SwanLab and launched via the `swanlab watch` command

## Architecture

### Backend Structure (`swanboard/`)

The backend is a FastAPI application with the following layers:

**Core Components:**
- `app.py` - FastAPI application instance with middleware stack and router registration
- `callback.py` - `SwanBoardCallback` class that connects SwanLab to the database, implements SwanKit callback interface
- `run/` - Server startup logic (`SwanBoardRun.run()`) with MySQL connection and uvicorn configuration

**Database Layer (`db/`):**
- Built on Peewee ORM with MySQL (via PyMySQL)
- Model files in `db/models/`: `Project`, `Experiment`, `Tag`, `Chart`, `Namespace`, `Source`, `Display`
- Base model class `SwanModel` (in `db/model.py`) provides utility methods for JSON conversion and automatic timestamp management
- Database connection configured via environment variables: `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT`

**API Layer:**
- `router/` - FastAPI routers for different resources (experiment, project, namespace, chart, media)
- `controller/` - Business logic for handling requests
- `middleware/common.py` - Custom middleware for response formatting, static file serving, error handling, logging, and parameter validation

**Middleware Stack (applied in order):**
1. `resp_base` - Adjusts response results, adds processing time
2. `resp_static` - Handles static file serving (skips API requests)
3. `catch_error` - Exception handling and error message formatting
4. `log_print` - Request/response logging
5. `resp_params` - Parameter validation error restructuring

**Configuration:**
- `settings.py` - File paths for static files (compiled Vue app in `template/`), experiment directories, and media storage

### Frontend Structure (`vue/`)

Vue 3 application with the following structure:

**Main directories:**
- `src/api/` - API client for backend communication
- `src/charts/` - Chart visualization components (line, image, audio, text charts using @antv/g2plot)
- `src/components/` - Reusable UI components (SLButton, SLModal, SLIcon, etc.)
- `src/layouts/` - Page layouts (MainLayout, ExperimentLayout, HomeLayout)
- `src/views/` - Page components organized by route
- `src/store/` - Pinia state management
- `src/router/` - Vue Router configuration
- `src/i18n/` - Internationalization

**Build Configuration:**
- Vite build system (see root `vite.config.js`)
- Root is `vue/` directory
- Build output: `swanboard/template/` (consumed by FastAPI for static serving)

## Development Workflow

### Backend Development

**Running the development server:**
```bash
cd test
python start_server.py  # Runs on http://127.0.0.1:6092
```

**Environment variables for MySQL:**
```bash
export MYSQL_DATABASE=swanlab
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_HOST=host.docker.internal  # or localhost
export MYSQL_PORT=3306
```

**Code style and linting:**
```bash
black swanboard              # Format (line-length: 120)
ruff check swanboard         # Lint
```

**Running backend tests:**
```bash
pytest test/unit             # Run all unit tests
pytest test/unit/db          # Run specific test directory
pytest test/unit/db/test_connect.py  # Run single test file
```

### Frontend Development

**Development server:**
```bash
npm install                  # Install dependencies (if needed)
npm run dev                  # Runs on port 5175
```

**Build:**
```bash
npm run build                # Development build
npm run build.release        # Production build (removes console logs)
```

**Code quality:**
```bash
npm run fmt                  # Format with prettier
npm run test                 # Run tests with vitest
```

### Full Integration Workflow

1. Backend developers work in `swanboard/` directory
2. Frontend developers work in `vue/` directory
3. After frontend changes, run `npm run build.release` to compile to `swanboard/template/`
4. Test the integration
5. When both frontend and backend are complete, tests pass, merge to main
6. Create a tag (e.g., `v0.3.0`) to trigger PyPI publishing

## Database Models

The database has the following key relationships:

- **Project** → has many **Experiments**
- **Experiment** → has many **Tags**, **Charts**, **Namespaces**
- **Chart** ← **Source** → **Tag** (many-to-many relationship for multi-experiment comparisons)
- **Display** connects **Charts** to **Namespaces** (determines chart organization in UI)

**Important model behaviors:**
- All models inherit from `SwanModel` which auto-manages `create_time` and `update_time`
- Experiment lifecycle: status field (0=running, 1=completed, -1=error/stopped)
- During `on_log()`, the callback checks experiment status; if status ≠ 0, raises `KeyboardInterrupt` to stop logging

## Building and Publishing

**Local build:**
```bash
# Set version first
export VERSION=0.3.0
python build_pypi.py
```

**The build process:**
1. Installs npm dependencies (if needed)
2. Runs `npm run build.release`
3. Updates version in `swanboard/package.json`
4. Runs `python -m build` to create wheel and sdist

**Automated publishing:**
- Triggered by pushing tags matching `v*.*.*` (e.g., `v0.3.0`)
- See `.github/workflows/publish-to-pypi.yml`
- Builds frontend, updates version, publishes to PyPI, creates GitHub release

## Testing

**Backend tests:** Located in `test/unit/` with pytest configuration in `test/unit/conftest.py`
- Uses `tutils` module for test utilities (mock database, directory creation, cleanup)
- Tests use pytest fixtures for setup/teardown

**Frontend tests:** Run with `npm run test` (vitest)

## Key Dependencies

**Backend:**
- `fastapi` >= 0.110.1
- `uvicorn` >= 0.14.0
- `peewee` (ORM)
- `pymysql` (MySQL driver)
- `swankit` (SwanLab callback interface)
- `ujson`, `psutil`

**Frontend:**
- Vue 3 with Vite
- `@antv/g2plot` - Chart visualizations
- `pinia` - State management
- `vue-router` - Routing
- `axios` - HTTP client
- Tailwind CSS for styling

## Python Version Support

Python >= 3.8 (maintains compatibility with 3.8, 3.9, 3.10, 3.11, 3.12)

## Static Type Checking

**Pyright configuration in `pyproject.toml`:**
- Includes: `swanboard/**/*.py`

## Important Notes

- The `swanboard/template/` directory is generated by the Vue build process and should not be edited directly
- Version number is stored in `swanboard/package.json` and extracted by hatch during build
- MySQL connection defaults to `host.docker.internal` for Docker compatibility
- Frontend dev server proxies `/api` requests to backend (configured via `VITE_SERVER_PROXY` env var)
