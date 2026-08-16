# Azure Infra Provisioning Agent

A conversational agent that helps non-technical/semi-technical engineers provision Azure
resources through natural language. An LLM (OpenAI, function/tool-calling) collects and
validates structured requirements turn-by-turn against a JSON schema; a deterministic
(non-LLM) pipeline then renders Terraform, opens a GitHub PR, and — after `terraform plan`
review and human approval — applies it to Azure via GitHub Actions.

```
user chat  →  FastAPI /chat  →  OpenAI tool-calling loop
                                      │
                          get_resource_schema / validate_field / validate_requirements
                                      │
                          submit_requirements (user-confirmed, validated)
                                      │
                          Jinja2 render → .tf / .tfvars   (deterministic, no LLM)
                                      │
                          commit to feature branch → GitHub PR
                                      │
                          GitHub Actions: terraform plan → posted as PR comment
                                      │
                          human review/approval → merge
                                      │
                          GitHub Actions: terraform apply
```

## Supported resources

Currently only `azure_sql_database` (see `schemas/azure_sql_database.json`). Adding a new
resource type is schema-driven:

1. Add `schemas/<resource_type>.json` describing required/optional fields, enums, patterns.
2. Add `terraform_templates/<resource_type>/*.j2` (backend, variables, main, tfvars).

No Python code changes are needed for either the conversational or rendering side — both
`app/tools/schema_loader.py` and `app/submission/terraform_renderer.py` discover resource
types generically from those directories.

## Local setup

```bash
cp .env.example .env   # fill in OPENAI_API_KEY at minimum
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then either:
- open `http://127.0.0.1:8000/docs` and drive `POST /chat` from Swagger,
- run `python cli.py` for a faster terminal REPL, or
- run the Streamlit UI (see below) for a proper chat interface.

`SUBMIT_REQUIREMENTS_MODE` in `.env` controls how far a confirmed submission goes:

| Mode | Behavior |
|---|---|
| `stub` (default) | Logs the validated, normalized payload only. Safe with no other config filled in. |
| `render_only` | Also renders Terraform to `./rendered_output/<slug>/` for local inspection. No GitHub calls. |
| `full_pr` | Also opens a real GitHub PR. Requires `GITHUB_*` settings below. |

## Tests

```bash
pytest
```

## Frontend (Streamlit)

A chat UI at `frontend/streamlit_app.py`, styled to match the accelerator's
"blueprint" visual identity. It's a thin client — every reply and every
follow-up suggestion comes from the FastAPI `/chat` endpoint; the frontend
holds no business logic of its own.

```bash
pip install -r frontend/requirements.txt
uvicorn app.main:app --reload            # backend, in one terminal — http://127.0.0.1:8000
cd frontend && streamlit run streamlit_app.py   # UI, in another — http://127.0.0.1:8501
```

Open `http://127.0.0.1:8501` in your browser. The backend URL is configurable from
the app's sidebar if you need to point it somewhere other than the default.

The backend URL is configurable from the sidebar (defaults to
`http://127.0.0.1:8000`), so the same UI can point at a deployed backend once
one exists. It's a separate deployable from the FastAPI app — its own
`frontend/requirements.txt` and `frontend/.streamlit/config.toml` — so it can
ship to its own Azure Web App independently.

Follow-up suggestion chips (`suggested_followups` in the `/chat` response,
see `app/llm/followups.py`) are derived deterministically from the last
`validate_requirements`/`submit_requirements` tool result already in the
conversation — never from an extra LLM call.

## One-time Azure/GitHub setup (manual — not scripted by this app)

These are prerequisites for `full_pr` mode and for the GitHub Actions workflows in
`.github/workflows/` to actually run against your Azure subscription. None of this is
performed by the Python app itself.

1. **Terraform remote state storage** — create the resource group, storage account, and
   blob container that `terraform_templates/*/backend.tf.j2` references (must match
   `TERRAFORM_STATE_*` in `.env`):
   ```bash
   az group create -n rg-tfstate -l eastus
   az storage account create -n sttfstateexample -g rg-tfstate -l eastus --sku Standard_LRS
   az storage container create -n tfstate --account-name sttfstateexample
   ```

2. **Azure AD App Registration + OIDC federated credential** — this is what backs
   `azure/login@v2` in both workflows with no long-lived client secret:
   ```bash
   az ad app create --display-name azure-infra-provisioning-agent
   az ad sp create --id <appId>
   az role assignment create --assignee <appId> --role Contributor \
     --scope /subscriptions/<subscriptionId>
   az ad app federated-credential create --id <appId> --parameters '{
     "name": "pr-plan",
     "issuer": "https://token.actions.githubusercontent.com",
     "subject": "repo:<owner>/<repo>:pull_request",
     "audiences": ["api://AzureADTokenExchange"]
   }'
   az ad app federated-credential create --id <appId> --parameters '{
     "name": "main-apply",
     "issuer": "https://token.actions.githubusercontent.com",
     "subject": "repo:<owner>/<repo>:ref:refs/heads/main",
     "audiences": ["api://AzureADTokenExchange"]
   }'
   ```

3. **Repo variables** (Settings → Secrets and variables → Actions → Variables) in the
   target infra repo — non-sensitive under OIDC:
   `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.

   **Repo secret** (Settings → Secrets and variables → Actions → Secrets): `SQL_ADMIN_PASSWORD` —
   the SQL authentication admin password for every SQL server this pipeline creates (mapped to
   `TF_VAR_sql_admin_password` inside the workflows — see
   `terraform_templates/azure_sql_database/variables.tf.j2`). Never set via chat or committed to
   tfvars.

4. **GitHub Environment** named `production` (Settings → Environments) with required
   reviewers configured — this is the actual human-approval gate for `terraform-apply.yml`.

5. **Branch protection** on `main` requiring the `terraform-plan` check to pass before merge.

## Project layout

```
app/
  main.py             FastAPI app: POST /chat, GET /healthz
  config.py           Settings (pydantic-settings) — the only module that reads env vars
  session_store.py    in-memory dict[session_id -> messages]
  llm/                system prompt, tool schemas, OpenAI client, tool-calling loop, followups
  tools/               schema_loader, validators, dispatch registry
  submission/          terraform_renderer (Jinja2), github_client (PyGithub), submit_handler
schemas/                one JSON file per supported resource type
terraform_templates/    one Jinja2 template folder per resource type + a shared common/
frontend/               Streamlit chat UI — separate deployable, calls /chat only
  streamlit_app.py
  components/           branding (theme/fonts), api_client
  assets/                mark.svg, embedded font files
.github/workflows/       terraform-plan.yml, terraform-apply.yml
tests/                   pytest coverage for schema_loader, validators, renderer, orchestrator, followups, frontend smoke
```
