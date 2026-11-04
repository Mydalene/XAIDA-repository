# XAIDA demo script

**Suggested length:** 12–15 minutes  
**Audience:** auditors, audit managers, and deployment stakeholders  
**Demo data:** use a built-in sample dataset or another approved synthetic dataset. The application's development and research team has successfully completed the Commission's Information Technology Office (ITO) validation and authorization process. Use real or confidential audit data only when the organization has approved its processing and storage.

## Before the demo

- Start XAIDA using the approved deployment or local run instructions in [DEPLOYMENT.md](./DEPLOYMENT.md).
- Sign in with an authorized demo account and acknowledge the Security and Confidentiality Statement.
- For an AI-assisted demonstration, confirm that Vertex AI is enabled and approved for the demo environment. Otherwise, skip the assistant portion.
- Start with a clean session using **New analysis** in the sidebar. Confirm the action when prompted.
- Keep the sample data synthetic. If demonstrating feedback marked **Potentially unsupported** or **Unsure**, explain that XAIDA retains the rated user message and assistant response in the evaluation database for the configured retention period.

## 1. Welcome and workflow overview — 1 minute

**Say:**  
“XAIDA supports a staged audit workflow: load and prepare a dataset, review duplicates if present, run anomaly detection, examine explanations, record auditor assessments, and generate findings and reports. Readiness reflects completion of the workflow milestones; audit review is also required before the audit is marked ready.”

Point out the sidebar’s **New analysis** and **Log out** controls, then show the readiness status, progress indicator, and score breakdown in the evidence area.

## 2. Load a sample dataset — 1 minute

1. In the **Dataset** stage, choose a sample from **Or choose a sample dataset**. For example, select **Accounts Payable**.
2. Select **Load sample dataset**.
3. Show the dataset preview and the dataset status.

**Say:**  
“For this walkthrough I’m using a built-in sample. XAIDA records dataset versions and audit events as the workflow progresses.”

## 3. Prepare the data — 1–2 minutes

1. Select **Process Data Preparation**.
2. Review the preparation results and validation information in the **Data Processing** stage.
3. Select **Proceed To Duplicate Review** if duplicates were found. If none were found, select **Proceed To Analysis**.

**Say:**  
“Preparation and duplicate handling are separate readiness milestones. When duplicates exist, duplicate review receives its own portion of the readiness score.”

## 4. Review duplicates if needed — 1 minute

If duplicate records are detected:

1. Review the duplicate records in **Duplicate Review**.
2. Choose the appropriate strategy: **Retain All Duplicates**, **Remove Duplicate Copies**, or **Manual Duplicate Review**.
3. Complete any required confirmation, then select **Proceed To Analysis**.

**Say:**  
“The correct choice depends on the audit context. XAIDA makes the decision visible and records the selected workflow action; it does not determine the organization’s duplicate policy.”

If no duplicates are detected, mention that duplicate review is marked not required and continue.

## 5. Run anomaly detection and inspect explanations — 2 minutes

1. In **Anomaly Detection**, select **Run Analysis**.
2. Review the analysis results and flagged-record summary.
3. Select **Open Explainability** and inspect the explanations for flagged records.

**Say:**  
“Anomaly flags are indicators for auditor review, not audit conclusions. Explainability provides supporting context for why records were flagged.”

## 6. Complete auditor review — 2–3 minutes

1. Select **Open Audit Review**.
2. Review the flagged records, their evidence, and any generated explanations.
3. Use **Manual Review** to enter an assessment for each flagged record, such as **Confirmed Anomaly**, **Potential Finding**, **False Positive**, or **Requires Investigation**. Add comments where appropriate.
4. Select **Save Review Decisions** and confirm.

**Say:**  
“The auditor makes and records the assessment. XAIDA requires flagged records to be reviewed before findings can be generated; the system does not replace professional judgment.”

## 7. Generate findings and reports — 1–2 minutes

1. Select **Proceed To Findings** after the review is saved.
2. Review the findings register and its dataset-version references.
3. Select **Generate Report** and confirm.
4. Open **Reports** and demonstrate the available PDF and Excel downloads.

**Say:**  
“Findings and reports are generated from the reviewed audit data. Review exported files and handle them under your organization’s approved storage and sharing procedures.”

## 8. Show traceability and close — 1 minute

1. Open **Lineage** to show dataset versions and transformations.
2. Open **Audit Trail** to show the chronological workflow events.
3. Open the **XAIDA Vertex AI Assistant** for the guidance and interpretation demonstration below. Do this only when Vertex AI use is approved.
4. Close with the workflow status and readiness breakdown.

**Say:**  
“The readiness score summarizes completed workflow milestones. A high score alone does not mean the audit is ready: audit review must also be complete, and the auditor remains responsible for the final assessment.”

## Demonstrate the Vertex AI Assistant — 2 minutes

Open the **XAIDA Vertex AI Assistant** from the sidebar. Use the approved sample dataset and ask questions that support the audit workflow:

1. Ask for guidance, such as: **“Based on the current workflow status, what should I review next?”**
2. Ask for interpretation, such as: **“Explain why this transaction was flagged, using only the evidence shown in this audit.”**
3. If relevant, ask: **“What evidence supports this explanation, and what should I verify myself?”**

**Say:**  
“The Vertex AI Assistant can provide workflow guidance and explain audit evidence in context. Its responses are advisory, may be incomplete or incorrect, and must be checked against the source records. It does not make audit conclusions or replace auditor judgment.”

Point out the privacy reminder in the sidebar. Explain that relevant audit context may be sent to the organization's approved Vertex AI model when a question is submitted. Do not use this feature in the demo unless Vertex AI use and the data have been approved.

## About & feedback and the completion survey — 1 minute

1. Expand **About & feedback** in the sidebar.
2. Point out the maintainer/support information and the survey notice.
3. When the survey is active, point directly to the survey link shown in the app and invite attendees to complete it after the demonstration.

**Say:**  
“Before you leave, please complete the XAIDA feedback survey using the link shown here. Your feedback helps the development and research team improve the application. The survey is separate from audit findings and reports.”

**Survey link:** `[ADD THE APPROVED SURVEY URL HERE]`

The current application says the anonymous survey link is not active yet. Until the approved URL is added to the application, do not tell attendees that a working link is available or ask them to follow a placeholder. Update this script and the application notice after the URL is provided and verified.

## Optional: demonstrate response feedback

If the assistant is enabled and a response is available:

1. Expand **Rate this response** under an assistant response.
2. Select the grounding assessment that reflects the response and set a helpfulness rating.
3. If you select **Potentially unsupported** or **Unsure**, explain that the rated exchange is retained for authorized review in the evaluation store. Other conversation exchanges are not copied to the flagged-review table.

Do not deliberately label a response inaccurately just to demonstrate the feature.

## Presenter reminders

- Use only synthetic or specifically approved demo data.
- Do not describe anomaly flags or AI suggestions as confirmed findings.
- If a sample has no duplicates or no flagged records, explain that the related review is not required or not applicable and continue the workflow.
- Do not promise a fixed set of findings; results depend on the selected dataset and analysis.
- Avoid displaying credentials, secrets, or private Cloud Logging / database details during a public demo.
