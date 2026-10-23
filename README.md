# CIT3495 Project 1: Data Collection and Analytics System

**Group 13**: Nicholas, Thuc

A containerized microservice system. Users log in, enter course grades, and view analytics (per-course statistics) computed from those grades.

![Architecture](./docs/architecture.png)

## Services

| Service | Tech | Role | Exposed to host |
|---|---|---|---|
| `web-app` | Flask | One web app with both pages: **Enter Data** (`/home`) and **Show Results** (`/view`). Calls the auth service, writes grades to MySQL, triggers analytics, reads results from MongoDB. | `127.0.0.1:5000` only |
| `auth-service` | Node.js / Express | `POST /login` (bcrypt check, returns a JWT) and `POST /verify`. Creates the default user from environment variables on first start. | No |
| `analytics-service` | Flask | `POST /trigger-analytics`: reads grades from MySQL, computes statistics, stores them in MongoDB. | No |
| `mysql` | MySQL 8.0 | Users and grades. Volume `mysql_data`. | No |
| `mongodb` | MongoDB 6.0 | Analytics results. Volume `mongo_data`. | No |

**Data flow:** browser -> `web-app` -> `auth-service` (verify token) -> `web-app` writes the grade to MySQL -> `analytics-service` reads MySQL and writes results to MongoDB -> `web-app` reads MongoDB and shows them.

## Prerequisites
Docker Desktop (or Docker Engine) with Docker Compose v2. Nothing else is needed.

## Setup

1. Create an .env file:
   ```
   ni .env
   ```
2. Start everything:
   ```
   docker compose up -d --build
   ```
3. Wait until all five containers are `healthy`:
   ```
   docker compose ps
   ```
4. Open http://localhost:5000 and log in with the `ADMIN_USERNAME` / `ADMIN_PASSWORD` you set in `.env`.

`.env` is git-ignored. **Never commit real passwords or secrets.**

### Environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `MYSQL_ROOT_PASSWORD` | mysql | Root password (used only by the container itself and its health check) |
| `MYSQL_DATABASE` | all DB users | Database name (`analytics_db`) |
| `MYSQL_USER`, `MYSQL_PASSWORD` | web-app, auth-service, analytics-service | Limited application user (not root) |
| `FLASK_SECRET_KEY` | web-app | Flask session signing |
| `AUTH_TOKEN_SECRET` | auth-service | JWT signing key |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | auth-service | Default login. Only the bcrypt hash is stored in MySQL. |

Generate strong values with `openssl rand -hex 32` (or `python -c "import secrets;print(secrets.token_hex(32))"`).

## Common commands

```
docker compose up -d --build           # start
docker compose ps                      # status and health
docker compose logs -f web-app         # logs
docker compose down                    # stop, KEEP data
docker compose down -v --remove-orphans   # stop and DELETE all data (fresh start)
```

If you change `MYSQL_USER`/`MYSQL_PASSWORD` after the first start, run `docker compose down -v` once: MySQL only creates users on an empty volume.

## Tests

```
cd web-app
pip install -r requirements.txt
python test_app.py
```
The unit tests cover login, access control (no token, forged token, auth service down -> access denied), input validation, and parameterized SQL. Databases and the auth service are mocked, so no containers are needed.

## Security measures

- Containers run as a **non-root** user; app containers use a **read-only root filesystem** (`read_only: true`, `/tmp` as tmpfs), `cap_drop: ALL`, and `no-new-privileges`.
- **No secrets in images or git**: configuration comes from `.env` at runtime; `.dockerignore` keeps `.env` out of build contexts.
- **Least exposure**: only `web-app` publishes a port, bound to `127.0.0.1`. The `backend` network is `internal: true`, so databases and internal services have no route to or from the internet.
- **Least privilege**: services use a limited MySQL user, not root.
- Passwords are hashed with **bcrypt**; sessions use **JWTs**; the web app **fails closed** if the auth service is unreachable.
- Slim, pinned base images; multi-stage builds.
- Vulnerability scan with **Trivy** in CI.

## Reliability and persistence

- Health checks on every service; `depends_on: condition: service_healthy` gives a correct start order.
- `restart: unless-stopped` on every service.
- Named volumes `mysql_data` and `mongo_data` keep data across `docker compose down` / `up`. Only `down -v` deletes them.
- Resource limits (CPU and memory) and rotated logs on every service.

## CI/CD (GitHub Actions)

`.github/workflows/ci.yml` runs on every push and pull request:

1. **test**: unit tests.
2. **build-scan-publish** (matrix over the three images): build, **Trivy scan**, then multi-arch (amd64 + arm64) build and push to Docker Hub with `latest`, short-SHA, and version tags. Publishing is skipped on pull requests.

Required repository secrets: `DOCKER_USERNAME`, `DOCKER_PASSWORD` (a Docker Hub access token).

