FROM docker.io/library/python:3.13-slim

LABEL org.opencontainers.image.title="finwiz" \
      org.opencontainers.image.description="finwiz using crewAI — financial research/analysis crew" \
      org.opencontainers.image.source="https://github.com/fjacquet/finwiz" \
      org.opencontainers.image.licenses="MIT"

# git is needed at install time: crewai-custom-tools is a git+https dependency
# (see pyproject.toml), and python:*-slim ships without git. Without it the
# install fails with "Git executable not found".
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

# Fast, reproducible installs with uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# README.md is referenced by the hatchling build metadata, so it must be present.
COPY pyproject.toml README.md uv.lock ./
COPY src/ src/

# Install the app into the system environment. Resolves the same dependency set
# as CI (crewai + pydantic>=2.13); no dev/test groups.
RUN uv pip install --system --no-cache .

# The crew entrypoint (pyproject [project.scripts] kickoff = finwiz.main:kickoff).
# Runtime config (LLM / data-provider API keys) is supplied via environment
# variables at `docker run` time, e.g.:
#   docker run --rm --env-file .env ghcr.io/fjacquet/finwiz
ENTRYPOINT ["kickoff"]
