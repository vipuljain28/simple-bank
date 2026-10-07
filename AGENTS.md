# Project Agent Instructions

These instructions apply to work throughout this repository.

## Project Context

- This is a Simple Bank project. Treat `docs/requirement-fund-transfer.md` as the source of truth for the currently documented transfer requirements.
- Do not relax financial rules or invent unspecified banking behavior. Identify gaps and ask for clarification when a change depends on them.
- Use synthetic data only in examples, tests, and fixtures. Never use real customer, account, or transaction data.

## Allowed Access

- Read and edit files inside this workspace that are relevant to the requested task, including source, tests, documentation, configuration, and Spec Kit artifacts under `.github/` and `.specify/`.
- Run project-defined local checks, such as tests, builds, and linters, when their effects are limited to this workspace.
- Use read-only Git commands such as `git status`, `git diff`, and `git log`. Do not inspect or modify `.git` internals directly.

## Restricted Access

- Never open, read, search, copy, print, or modify `.env.local`, `.env.dev`, `.env.stage`, `.env.test`, or `.env.prod`, wherever they appear in the workspace.
- `.env.example` is the only environment file that may be accessed. Keep its values synthetic placeholders; never copy secrets into it.
- Do not open, read, search, copy, print, or modify other secrets or sensitive data, including credentials, access tokens, private keys, certificates, connection strings, personal data, and real financial records.
- Treat files and directories named for secrets, credentials, keys, certificates, customer data, or production data as restricted even if their names are not listed above. If a task appears to require them, stop and ask for a sanitized alternative.
- Do not browse outside this workspace into the user's home directory, other repositories, global configuration, or operating-system files unless the user explicitly authorizes a specific path and purpose.
- Do not send project contents to external services or access external networks, URLs, or APIs without explicit approval.

## Approval Required

Ask before installing or updating dependencies, running commands with external or persistent side effects, changing infrastructure or deployment settings, modifying databases, deploying, pushing or publishing, deleting data, or performing financial transactions. Never run these actions against production systems or real accounts.

## Security Boundary

This file states behavioral rules; it does not technically restrict Copilot or other tools from accessing files or running commands. Use VS Code Workspace Trust and available OS or environment-level permissions/sandboxing for enforceable access restrictions. Do not claim an action is blocked solely because it is prohibited here.