# XAIDA auditor deployment checklist

XAIDA is being prepared for Google Cloud Run with Vertex AI. Do not expose this
app to auditors until the platform owner has configured and verified the
controls below.

## Access and auditor isolation

- XAIDA requires authentication by default and supports both Streamlit OIDC
  sign-in and application-managed email/password accounts. Set
  `XAIDA_ALLOWED_EMAILS` to a comma-separated allowlist of approved auditor
  email addresses; it controls access for both methods and invitation-only
  local account registration. Keep the allowlist current when auditor access
  changes. OIDC is optional when using local accounts; to enable it, configure
  `redirect_uri`, a strong `cookie_secret`, and the OIDC provider's `client_id`,
  `client_secret`, and `server_metadata_url` in the protected
  `.streamlit/secrets.toml` `[auth]` section. For Cloud Run, mount that file
  from Secret Manager at `/app/.streamlit/secrets.toml`; never bake or commit
  the secrets file.
- Local accounts store salted PBKDF2 password hashes (never plaintext) in the
  configured XAIDA database. Use the durable PostgreSQL backend for deployed
  services; SQLite is intended for local development and must not be used as
  ephemeral or shared production account storage. Removing an email from
  `XAIDA_ALLOWED_EMAILS` immediately blocks both local and OIDC access.
- Alternatively, a trusted identity proxy may be used only if it enforces
  authenticated, authorized access before requests reach XAIDA; document and
  test the proxy controls and do not rely on user-supplied identity headers.
- Do not publish the app anonymously. Test login, denied access, and logout
  before permitting audit data.
- For Cloud Run, keep `XAIDA_REQUIRE_AUTH=true` and configure a non-empty
  `XAIDA_ALLOWED_EMAILS`. Use an identity-aware proxy or Cloud Run IAM
  invocation controls where appropriate; ensure the selected ingress/auth
  configuration still permits the intended auditors to reach XAIDA's own
  sign-in page. Apply edge rate limits to public sign-in endpoints.
- For local development with synthetic data only, `XAIDA_REQUIRE_AUTH=false`
  disables the authentication gate. Never use that setting for an exposed or
  real-data deployment.
- Verify with two separate auditor identities that each saved audit is bound
  to its signed-in auditor and cannot be loaded by another user.
- For Cloud Run, set `XAIDA_SESSION_STORAGE_BACKEND=gcs` and
  `XAIDA_DATABASE_BACKEND=postgres`. XAIDA autosaves each active audit to the
  private bucket and stores an owner hash, object reference, and expiration in
  Cloud SQL. A signed-in auditor can resume the same audit using its session
  URL after an instance restart. Do not use shared URLs as authorization; the
  owner check is enforced by Cloud SQL.
- Saved audit data expires after 24 hours without an autosave. The
  `Exit and delete audit data` button, Reset, and New Analysis delete the
  current audit-session row and all Cloud Storage object generations under its
  random session ID. Evaluation records are deliberately kept according to
  `XAIDA_EVALUATION_RETENTION_DAYS`.
- Cloud Storage lifecycle deletion is asynchronous. Configure the supplied
  [gcs-lifecycle.json](./gcs-lifecycle.json) and run the expired-session
  cleanup job regularly. Validate deletion behavior against the organization's
  erasure requirements before using real audit data.

## Audit data and AI service

- Use synthetic or de-identified datasets until the organization approves the
  hosting environment and Vertex AI service for real audit data.
- XAIDA sends audit context and relevant evidence to Vertex AI when users ask
  questions through the Vertex AI assistant or request recommendations. The app
  refuses to create a
  Vertex AI client unless `XAIDA_VERTEX_AI_APPROVED=true`. Set it only after
  confirming the GCP project, region, access policy, retention settings, and
  data-handling terms meet the organization's requirements.
- The default model is `gemini-3.5-flash-lite`. Configure
  `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, and optionally
  `XAIDA_VERTEX_AI_MODEL` as Cloud Run environment variables. Grant the Cloud
  Run service account the Vertex AI User role on the approved project. The
  Google Gen AI SDK uses Application Default Credentials; do not place a
  service-account key in the image or environment.
- For local development, copy `.env.example` to `.env`, install the project
  requirements, and authenticate with Google Cloud CLI Application Default
  Credentials using `gcloud auth application-default login`. Ensure the
  selected Google account has permission to use Vertex AI in the configured
  project and that the Vertex AI API is enabled. Keep
  `XAIDA_VERTEX_AI_APPROVED=false` until organizational data-transfer approval
  is confirmed.
- Set `XAIDA_VERTEX_AI_APPROVED=true` only after review; otherwise Vertex AI
  assistant requests remain disabled. `.env.example` documents the local configuration
  names. Never commit `.env` or Streamlit secrets files.
- Deploy the container to Cloud Run with the platform-provided `PORT`, TLS,
  and restricted ingress/invocation policy required by the organization.
  XAIDA enforces its email allowlist for both OIDC and local accounts; keep
  that application-level check enabled even when an identity-aware proxy is
  used.
- Test the model and region with XAIDA's grounding and assistant tests. The
  Flash-Lite model may ignore custom sampling settings; XAIDA relies on its
  response validation and evidence-grounding safeguards as well as model
  behavior.

## Runtime and operations

- Locally, XAIDA stores Vertex AI assistant evaluation metadata in SQLite at
  `data/xaida_evaluations.sqlite3`. In Cloud Run, set
  `XAIDA_DATABASE_BACKEND=postgres` and connect it to the Cloud SQL database.
  Evaluation events, auditor ratings, and aggregate audit-review metrics are
  stored in PostgreSQL. Set `XAIDA_EVALUATION_RETENTION_DAYS` to the approved
  positive number of days; the default is 365 days. Expired evaluation records
  are purged when the store is accessed. Invalid retention settings stop writes
  with an explicit configuration error.
  The store contains random interaction and pseudonymous session IDs,
  timestamp, workflow stage, response category, rating, latency,
  success/error category, and app version. When grounding feedback is
  `Potentially unsupported` or `Unsure`, the rated user message and assistant
  response are also stored in `flagged_interaction_reviews` for review. Other
  conversations are not copied into that table. The flagged exchange is
  retained for the same `XAIDA_EVALUATION_RETENTION_DAYS` period and should
  only be accessed by authorized reviewers. Evaluation storage does not
  include dataset rows, API keys, or raw exception details.
  Authorized reviewers can retrieve flagged exchanges with:

  ```sql
  SELECT r.captured_at, r.interaction_id, r.grounding_rating,
         e.workflow_stage, e.response_category,
         r.user_message, r.assistant_response
  FROM flagged_interaction_reviews AS r
  JOIN interaction_evaluations AS e USING (interaction_id)
  ORDER BY r.captured_at DESC;
  ```
- Aggregate audit-review metrics are also stored in this database, keyed by
  audit-session ID and dataset version. These metrics include record counts and
  auditor assessment totals; dataset rows, comments, and other free text are
  not written to the metrics table. The same configured retention period
  applies to these aggregate metric snapshots.
- Treat the evaluation database as operational assessment data: restrict
  database access, approve the retention period, and configure Cloud SQL
  backups, point-in-time recovery, and monitoring.
- Audit-session snapshots contain uploaded data, analysis results, review
  decisions, findings, the audit log, and assistant conversation. They are
  compressed JSON in Cloud Storage, not SQLite or Cloud SQL payloads. Snapshot
  encoding rejects unsupported values rather than silently dropping them.
- Grant the Cloud Run runtime service account `roles/cloudsql.client` on the
  project, `roles/storage.objectAdmin` on the dedicated bucket, and
  `roles/aiplatform.user` on the Vertex AI project. Give the service account
  access to the Cloud SQL password secret. Do not grant the application
  service account broad project-owner permissions.
- Create a dedicated PostgreSQL database named `xaida` and login `xaida_app`
  on the existing PostgreSQL 18 Cloud SQL instance. Store the database
  password in Secret Manager, and attach the instance to the Cloud Run service
  so the app can connect over `/cloudsql/PROJECT:REGION:INSTANCE`.
- Create the bucket as private, uniform bucket-level access, public access
  prevention enabled, and with an organization-approved encryption policy.
  The lifecycle rules in `gcs-lifecycle.json` delete objects and older object
  generations after one day. Configure bucket versioning only if the
  noncurrent-generation lifecycle rule is also active.
- Configure a Cloud Run Job using the same image, service account, database
  settings, and bucket settings with command:

  ```text
  python -m assistant.session_persistence --cleanup-expired
  ```

  Schedule it at least hourly. It removes expired session metadata and any
  remaining objects; Cloud Storage lifecycle is a second cleanup mechanism.
- XAIDA authenticates users through OIDC or application-managed accounts when
  required, but does not associate evaluator identities with evaluation rows.
  Evaluation sessions use random pseudonymous IDs and cannot be attributed to
  an auditor by XAIDA.
- The sidebar About & feedback section currently identifies the maintainer as
  the anonymous XAIDA Project Team and directs users to their deployment
  administrator for support. Completed audits display an optional anonymous
  survey notice. The anonymous survey link is not active yet.
  When finalized, verify the survey provider does not collect identifying
  information and keep survey responses separate from evaluation events,
  findings, and audit reports.
- If an evaluation write fails, the Vertex AI assistant continues to operate and shows an
  administrator-facing warning; feedback-save failures are also shown to the
  user.
- Install dependencies from `requirements.txt` in a supported Python
  environment and run the test suite before each release:

  ```powershell
  python -m pytest -q
  ```

- Start the application with:

  ```powershell
  streamlit run app.py
  ```

- The root `Dockerfile` builds the Cloud Run container and honors the
  platform-provided `PORT`. Build and deploy it using the organization's
  approved Cloud Build/Artifact Registry workflow. Configure Cloud Run
  environment variables and service-account IAM through the platform rather
  than baking deployment-specific values into the image.
- Required Cloud Run environment values include
  `XAIDA_REQUIRE_AUTH=true`, `XAIDA_ALLOWED_EMAILS`,
  `XAIDA_DATABASE_BACKEND=postgres`,
  `CLOUD_SQL_CONNECTION_NAME=PROJECT:REGION:INSTANCE`,
  `XAIDA_DATABASE_NAME=xaida`, `XAIDA_DATABASE_USER=xaida_app`,
  `XAIDA_SESSION_STORAGE_BACKEND=gcs`,
  `XAIDA_SESSION_STORAGE_BUCKET=xaida-storage`,
  `XAIDA_SESSION_RETENTION_HOURS=24`, `GOOGLE_CLOUD_PROJECT`,
  `GOOGLE_CLOUD_LOCATION`, `XAIDA_VERTEX_AI_MODEL`, and
  `XAIDA_VERTEX_AI_APPROVED`. Inject `XAIDA_DATABASE_PASSWORD` from Secret
  Manager; do not put credentials in the container image or source.
- The container runs as an unprivileged user. Deploy with a dedicated runtime
  service account and only the documented Cloud SQL, Storage, Vertex AI, and
  Secret Manager permissions; scope resource access to the application
  database and session bucket.

- Set the upload-size limit on the hosting platform to a value approved for
  expected audit files; validate memory requirements using representative
  datasets before deployment.
- Monitor server-side errors without logging uploaded row contents, API keys,
  or full assistant prompts.
- Define an approved retention and deletion process for session data, uploaded
  files, logs, and downloaded reports before using real audit data.
- CSV downloads from the evidence panel prefix spreadsheet-formula-like text
  with an apostrophe to reduce formula-injection risk when opened in spreadsheet
  software.
