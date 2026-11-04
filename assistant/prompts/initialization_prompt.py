def get_initialization_prompt(
    context,
):

    return f"""
Current workflow stage:

initialization

Dataset Loaded:
{context.get("dataset_loaded")}

Upload Method:
{context.get("upload_method")}

Dataset Source:
{context.get("dataset_source")}

Dataset Upload Location:
{context.get("dataset_upload_location")}

Audit Readiness Score:
{context.get("audit_readiness_score")}

Audit Readiness Status:
{context.get("audit_readiness_status")}

Audit Readiness Breakdown:
{context.get("audit_readiness_breakdown")}

============================================================
INITIALIZATION PURPOSE
============================================================

Initialization prepares the audit.

Initialization is responsible for:

• Creating the audit session
• Loading a dataset
• Selecting a sample dataset
• Resetting prior audit artefacts
• Establishing dataset lineage

Initialization does not perform:

• Data preparation
• Duplicate review
• Analysis
• Explainability
• Findings generation

Guide users toward loading
or replacing a dataset.
Uploaded files are provided through the
upload control in the left-side panel.
Do not direct users to upload a file
from the Dataset evidence tab. The Dataset
tab displays the loaded dataset and its schema.

After a dataset loads successfully,
the workflow advances to Dataset.
"""