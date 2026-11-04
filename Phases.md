Phase 1: Audit Session Foundation

Before:
Vertex AI assistant
Analytics
Duplicates
Reports

we need:
Audit Session

because everything in XAIDA revolves around the current audit.

Step 1: Define the Audit Session Object
Replace scattered Streamlit state variables with a single object.
AuditSession

Structure:
AuditSession

├── metadata
├── dataset
├── duplicates
├── analysis
├── findings
├── explainability
├── reporting
└── conversation

Step 2: Folder Structure

Create:
assistant/
├── audit_session.py
├── session_manager.py
├── context_builder.py
├── intent_router.py
└── copilot.py

But initially implement only:
audit_session.py
session_manager.py


Step 3: AuditSession Class
Nothing more complicated initially.

Step 4: Metadata Structure

Step 5: Dataset Context

Step 6: Duplicate Context

Step 7: Analysis Context

Step 8: Findings Context

This is new in XAIDA 4.0.

Step 9: Explainability Context  

Step 10: Conversation Context


AuditSession.metadata

{
    "session_id": "",

    "audit_name": "",

    "created_at": "",

    "last_updated": "",

    "workflow_stage": "new_audit",

    "status": "active"
}

AuditSession.dataset

{
    "dataset_name": "",

    "rows": 0,

    "columns": 0,

    "quality_score": 0,

    "dataframe": None,

    "profile": {}
}

AuditSession.duplicates

{
    "duplicate_count": 0,

    "duplicate_groups": 0,

    "strategy": None,

    "records_removed": 0,

    "review_complete": False,

    "duplicate_records": None
}

AuditSession.analysis

{
    "analysis_complete": False,

    "latent_features": None,

    "risk_scores": None,

    "risk_distribution": {},

    "analysis_dataset": None
}
AuditSession.findings

{
    "open": [],

    "validated": [],

    "dismissed": [],

    "needs_review": []
}

AuditSession.explainability

{
    "shap_values": None,

    "top_features": None,

    "narratives": []
}

AuditSession.conversation

[
    {
        "role": "user",
        "content": "Upload Accounts Payable"
    },

    {
        "role": "assistant",
        "content": "Dataset uploaded successfully"
    }
]



Suggested Immediate Improvement
Add a helper.
Create:
def get_session():

    return (
        st.session_state.audit_session
    )

inside:

assistant/session_manager.py

Then everywhere in XAIDA:

from assistant.session_manager import (
    get_session
)

session = get_session()
instead of: st.session_state.audit_session
This makes future migrations easier.

orchestration/workflow_engine.py
Current Stage
↓
Validate Transition
↓
Move To Next Stage

Phase 2: Context Builder
Not the Vertex AI assistant yet.
The Vertex AI assistant cannot work until you can reliably convert the current audit state into AI context.

Why Context Builder Comes Next
Current flow:

Audit Session
        ↓
Workflow Engine
        ↓
Context Builder
        ↓
Vertex AI assistant

Without a Context Builder, the Vertex AI assistant will end up reading:
session.dataset
session.analysis
session.findings
directly and become tightly coupled to the backend.

We want: context = build_context(session)
and only then:
response = copilot.chat(
    user_message,
    context
)

assistant/context_builder.py

Initial version:
def build_context(session):

    return {

        "workflow_stage":
            session.metadata[
                "workflow_stage"
            ],

        "dataset_name":
            session.dataset[
                "dataset_name"
            ],

        "rows":
            session.dataset[
                "rows"
            ],

        "columns":
            session.dataset[
                "columns"
            ],

        "quality_score":
            session.dataset[
                "quality_score"
            ],

        "duplicate_count":
            session.duplicates[
                "duplicate_count"
            ],

        "duplicate_groups":
            session.duplicates[
                "duplicate_groups"
            ],

        "risk_level":
            session.analysis[
                "risk_level"
            ],

        "validated_findings":
            len(
                session.findings[
                    "validated"
                ]
            ),

    }

Future Context Package
Eventually:
{
    "workflow_stage": "...",

    "dataset_summary": {},

    "duplicate_summary": {},

    "analysis_summary": {},

    "risk_distribution": {},

    "top_findings": [],

    "finding_status": {},

    "explainability_summary": {},

    "auditor_decisions": []
}


Phase 3: Intent Router
After Context Builder.

Create:
assistant/
    intent_router.py
``

Purpose:
Map conversation
        ↓
Workflow action

Example:

User:
Retain all duplicates.

Output:
{
    "intent":
        "retain_all_duplicates"
}

No Vertex AI integration yet.
Start with simple rules.




Suggested Immediate Improvement
Add a helper.
Create:
def get_session():

    return (
        st.session_state.audit_session
    )

inside:

assistant/session_manager.py

Then everywhere in XAIDA:

from assistant.session_manager import (
    get_session
)

session = get_session()
instead of: st.session_state.audit_session
This makes future migrations easier.

orchestration/workflow_engine.py
Current Stage
↓
Validate Transition
↓
Move To Next Stage

Phase 2: Context Builder
Not the Vertex AI assistant yet.
The Vertex AI assistant cannot work until you can reliably convert the current audit state into AI context.

Why Context Builder Comes Next
Current flow:

Audit Session
        ↓
Workflow Engine
        ↓
Context Builder
        ↓
Vertex AI assistant

Without a Context Builder, the Vertex AI assistant will end up reading:
session.dataset
session.analysis
session.findings
directly and become tightly coupled to the backend.

We want: context = build_context(session)
and only then:
response = copilot.chat(
    user_message,
    context
)

assistant/context_builder.py

Initial version:
def build_context(session):

    return {

        "workflow_stage":
            session.metadata[
                "workflow_stage"
            ],

        "dataset_name":
            session.dataset[
                "dataset_name"
            ],

        "rows":
            session.dataset[
                "rows"
            ],

        "columns":
            session.dataset[
                "columns"
            ],

        "quality_score":
            session.dataset[
                "quality_score"
            ],

        "duplicate_count":
            session.duplicates[
                "duplicate_count"
            ],

        "duplicate_groups":
            session.duplicates[
                "duplicate_groups"
            ],

        "risk_level":
            session.analysis[
                "risk_level"
            ],

        "validated_findings":
            len(
                session.findings[
                    "validated"
                ]
            ),

    }

Future Context Package
Eventually:
{
    "workflow_stage": "...",

    "dataset_summary": {},

    "duplicate_summary": {},

    "analysis_summary": {},

    "risk_distribution": {},

    "top_findings": [],

    "finding_status": {},

    "explainability_summary": {},

    "auditor_decisions": []
}

Phase 3: Intent Router
After Context Builder.

Create:
assistant/
    intent_router.py
``

Purpose:
Map conversation
        ↓
Workflow action

Example:

User:
Retain all duplicates.

Output:
{
    "intent":
        "retain_all_duplicates"
}

No Vertex AI integration yet.
Start with simple rules.


Phase 4: Action Router
This becomes the bridge:
Intent
    ↓
Workflow Engine
    ↓
Dataset Services
    ↓
Analytics Services

Phase 5: Vertex AI assistant
Create:
assistant/copilot.py

Architecture:
User Message
        ↓
Context Builder
        ↓
Vertex AI
        ↓
Intent Router
        ↓
Action Router
        ↓
Workflow Engine

This is the point where XAIDA gains its Vertex AI-powered audit assistant.

Recommended Build Order
✅ audit_session.py

✅ session_manager.py

✅ workflow_engine.py

⬜ context_builder.py    ← NEXT

⬜ intent_router.py

⬜ action_router.py

⬜ dataset_services/     

⬜ analytics_services/

⬜ copilot.py

⬜ evidence_workspace

⬜ reporting

assistant/intent_router.py
Purpose:
User Message
      ↓
Intent
      ↓
Action

assistant/copilot.py
Purpose:
Conversation
+
Context
+
Vertex AI


For XAIDA 4.0, action_router.py should be the single orchestration point between:
Intent Router
      ↓
Action Router
      ↓
Workflow Engine
      ↓
Services


XAIDA 4.0 Flow
User:
"Retain all duplicates"

        ↓

Intent Router

{
    intent:
    retain_all_duplicates
}

        ↓

Action Router

        ↓

Duplicate Service

        ↓

Workflow Engine

duplicate_review
        ↓
analysis_dataset

        ↓

Vertex AI assistant

"All duplicate records have been retained.
The analysis dataset is ready."



assistant/prompts.py
Future enhancement

Later:
build_system_messages()

should become:
build_messages(
    context
)

and dynamically inject:
get_duplicate_review_prompt()
get_analysis_summary_prompt()
get_finding_validation_prompt()
get_reporting_prompt()

based on:
workflow_stage

Currently you're only injecting:
get_system_prompt()
get_workflow_prompt()

which is fine for Phase 1.

conversation_manager.py should be responsible for conversation storage and retrieval only.

It should not:

Call Vertex AI
Detect intents
Execute actions
Change workflow stages

Its job is:
Conversation History
        ↓
Store
Retrieve
Trim
Clear

Build Evidence Panel First
Create:

ui/
    evidence_panel.py
Initial version:
def render_evidence_panel(
    session
):
Display:
Audit Information

Reading directly from: session
Workflow Stage
Dataset Name
Rows
Duplicate Count
Risk Level

Example
Current screenshot:
Right panel should show:
Audit Summary

Workflow:
new_audit

Dataset:
-

Rows:
0

Duplicates:
0

Risk Level:
-

Why This Next?
Because XAIDA's architecture is:
Vertex AI assistant
        +
Evidence
not:
Chat only

The user should always see:
Current Audit State
without asking XAIDA.

Then Build Dataset Upload
After Evidence Panel:
dataset/
integration.

Add:
Upload Dataset
Then update:
session.dataset

instead of:
st.session_state.dataset

New Workflow
New Audit
      ↓
Upload Dataset
      ↓
Data Preparation
      ↓
Duplicate Review
      ↓
Analysis

All powered by:
AuditSession


After Evidence Panel
The next major feature should be:
Dataset Upload
which introduces:
session.dataset["dataframe"]
and transitions:
new_audit
    ↓
data_preparation

new_audit
    ↓
data_preparation

Now we're at the first real XAIDA 4.0 feature:
Dataset Upload Integration
Until now you've built:

Audit Session
Workflow Engine
Vertex AI assistant
Evidence Panel

But XAIDA doesn't yet have audit data.
Create ui/dataset_upload.py

Expected Behaviour
Initial:
Workflow Stage
new_audit

After upload:
Workflow Stage
data_preparation

Evidence Panel:
Dataset

AP.xlsx

Rows
800

Columns
12

Next After Upload Works
Build:
dataset/
    data_preparation_service.py

which will eventually perform:
Missing Values
Data Quality
Column Validation
Dataset Profiling
and update: session.dataset["quality_score"]

Then the Vertex AI assistant can say:
Dataset uploaded successfully.

I analysed 800 records.

Data quality score: 98%.

No major quality issues were found.

Proceed to duplicate review?

XAIDA 4.0 Evidence Rules
Session Start

Show only:
Audit Evidence

No evidence available.

Upload a dataset to begin
the audit workflow.

A Refresh Analysis Run is a good idea, but it should only reset analysis-related artefacts, not the dataset evidence.
Recommended Behaviour
When the auditor clicks: Refresh Analysis

XAIDA should: 
Keep:
✅ Dataset
✅ Dataset Profile
✅ Duplicate Review
✅ Analysis Dataset

Reset:
❌ Analysis Results
❌ Findings
❌ Explainability
❌ Reports

Then:
▶ Run Analysis Again

1. Refresh Analysis
Purpose:
Keep current audit session
Keep current dataset
Keep duplicate decisions
Keep analysis dataset

Delete:
- analysis results
- findings
- explainability
- reports

Immediately rerun analysis

Workflow:
Refresh Analysis
↓
Clear analysis artefacts
↓
Run Analysis
↓
New Results

This is essentially: Recalculate


2. New Analysis
Purpose: Start a completely fresh audit cycle

Delete:
Dataset
Duplicates
Analysis Dataset
Analysis
Findings
Explainability
Reports
Conversation
Recommendations

Return to: workflow_stage = "new_audit"

Workflow:
New Analysis
↓
Confirm
↓
Reset Session
↓
Back to Upload Dataset

Equivalent to: Start New Audit

In your current XAIDA workflow, the Data Preparation phase is doing much more than simply loading a file.
Based on the code and the evidence shown in your screenshots, the following occurs during Data Preparation:
1. Dataset Validation
XAIDA executes:
validate_dataset(
    dataframe
)

This checks the uploaded dataset and produces validation information used later for quality scoring.

2. Data Quality Assessment
XAIDA calculates:
calculate_data_quality_score(
    validation
)

This produces: Quality Score: 93

which is currently displayed in your Data Preparation evidence section.

3. Dataset Profiling
XAIDA generates a profile:
generate_dataset_profile(
    dataframe
)

This profile can contain information such as:
Rows
Columns
Numeric Columns
Categorical Columns
Memory Usage

and is stored in: session.dataset["profile"]

4. Duplicate Detection
XAIDA executes:
detect_duplicates(
    dataframe
)

which produces: duplicates

and stores:
session.duplicates["duplicate_count"]
session.duplicates["duplicate_groups"]
session.duplicates["duplicate_records"]

From your screenshot, the actual result is:

Duplicate Records: 19
Duplicate Groups: 3

and the duplicate preview table confirms duplicate records were identified.

5. Evidence Generation
The Data Preparation stage creates audit evidence:
Dataset
Data Preparation
Duplicate Preview

The auditor should review this evidence before deciding what to do with duplicates.

6. Auditor Decision Point
This is where the workflow should pause.
The auditor should see:
Data Preparation Completed

Quality Score: 93
Duplicate Records: 19
Duplicate Groups: 3

Then choose:
Proceed To Duplicate Review
because duplicates exist.
If duplicate count were zero: Proceed To Analysis Dataset
would be the correct next action.

What SHOULD NOT happen in Data Preparation
The following should NOT occur yet:
Drop duplicates
Retain duplicates
Run analysis
Generate findings
Generate SHAP explanations
Generate reports
Those belong to later workflow stages.

Recommended XAIDA Workflow
Upload Dataset
        ↓
Data Preparation
        ↓
Review Evidence
        ↓
Duplicate Review
        ↓
Retain All
Drop All
Per-Row Review
        ↓
Analysis Dataset
        ↓
Run Analysis
        ↓
Findings
        ↓
Explainability
        ↓
Reporting

Given your current screenshots, Data Preparation is already successfully producing evidence:
Quality Score = 93
Duplicate Records = 19
Duplicate Groups = 3

The remaining issue is workflow control: XAIDA should now route the auditor to Duplicate Review, not directly to Analysis Dataset.

I completely agree. In an audit workflow, Data Preparation should not merely detect null values, it should actively assess and prepare them for analysis.
For XAIDA, I would make Data Preparation perform the following:
1. Missing Value Assessment
Generate evidence such as:
Missing Values Analysis

Column          Missing
--------------------------------
PaidDate        312
Terms           0
Currency        0
Amount          0

Total Missing Values: 312
Affected Records: 312

Store:
session.dataset[
    "missing_values"
] = missing_summary

2. Missing Value Classification

Not all nulls are data quality issues.

Example from your Accounts Payable dataset:
PaidDate = NaT
Status = Open

This is valid.

Invoice not yet paid.

Therefore: Business-Valid Missing Values

should be separated from: Unexpected Missing Values
Unexpected Missing Values

Example:
PaidDate
Status = Open
→ Valid

InvoiceDate
→ Invalid

Amount
→ Invalid

3. Imputation Recommendations
XAIDA should recommend treatment:
Column         Action
--------------------------------
PaidDate       Retain Null
Terms          Fill Mode
Amount         Manual Review
Currency       Manual Review

Store:
session.dataset[
    "null_recommendations"
]

4. Imputation Execution
Before analysis:
Numeric columns:
df[col] = (
    df[col]
    .fillna(
        df[col].median()
    )
)

Categorical columns:
df[col] = (
    df[col]
    .fillna(
        "Unknown"
    )
)

Dates:
df[col] = (
    df[col]
    .fillna(
        pd.Timestamp(
            "1900-01-01"
        )
    )
)

or preserve if business-valid.

5. Null Value Evidence Panel

Add a new section:
Data Preparation

Quality Score: 93

Duplicate Records: 19

Missing Values

PaidDate: 312
Terms: 0
Amount: 0

Treatment Applied

PaidDate:
Retained (Business Valid)

Amount:
No Action

6. Save Prepared Dataset

After all preparation:
session.analysis[
    "analysis_dataset"
]

should contain:
Validated Dataset
+
Null Treatment
+
Duplicate Decisions

This becomes the governed dataset used by:
run_analysis(
    session
)

Recommended Data Preparation Workflow
Upload Dataset
        ↓
Validation
        ↓
Profile Dataset
        ↓
Missing Value Assessment
        ↓
Missing Value Treatment
        ↓
Duplicate Detection
        ↓
Duplicate Review
        ↓
Analysis Dataset


For your current Accounts Payable dataset, the first thing XAIDA should flag is the large number of:
PaidDate = NaT

entries visible in the duplicate preview, and classify most of them as business-valid nulls because unpaid invoices legitimately have no payment date.

New Module
dataset/imputation_rules.py

Future Enhancement
Allow auditors to edit rules from the UI:
session.dataset[
    "imputation_rules"
]

Example:
{
    "Amount": {
        "strategy": "median"
    },

    "PaidDate": {
        "strategy": "retain"
    },
Here's a production-ready XAIDA preprocessing module that safely handles:

✅ Numeric columns
✅ Categorical columns
✅ Boolean columns
✅ Date columns
✅ Date-derived audit features
✅ Missing dates (NaT)
✅ SHAP feature names
✅ Anomaly Detection pipeline compatibility

Audit-specific Features Created

For your AP dataset, the model will automatically generate:

Days_To_Due
Days_To_Payment

InvoiceDate_Year
InvoiceDate_Month
InvoiceDate_Quarter
InvoiceDate_Weekday
InvoiceDate_Day

DueDate_Year
DueDate_Month
DueDate_Quarter
DueDate_Weekday
DueDate_Day

PaidDate_Year
PaidDate_Month
PaidDate_Quarter
PaidDate_Weekday
PaidDate_Day

Log_Amount



XAIDA Architecture Recommendation
Step 1
features, feature_names = (
    transform_features(
        dataframe
    )
)

Step 2

Create: analytics/autoencoder.py

Step 3

Update anomaly_detection.py
ensemble_scores = (

    isolation_weight
    * isolation_scores_scaled

    +

    kmeans_weight
    * kmeans_scores_scaled

    +

    autoencoder_weight
    * autoencoder_scores_scaled
)

isolation_weight=0.4
kmeans_weight=0.2
autoencoder_weight=0.4

Step 4

Add Results to Findings

Show:
Isolation Forest Score

KMeans Score

Autoencoder Error

Ensemble Score

in the anomaly table.

Example:

APID	IF	KMeans	Autoencoder	Ensemble
AP10025	0.87	0.72	0.94	0.88

This is extremely useful for auditors.

Step 5

Explainability

SHAP currently explains: Isolation Forest

You can retain that.

The auditor only needs: Why was AP10025 flagged?
not: Which model flagged it?

My final XAIDA recommendation

Version 4.0:
Preprocessing
      ↓
Feature Engineering
      ↓
Autoencoder
      ↓
Isolation Forest
      ↓
KMeans Distance
      ↓
Weighted Ensemble
      ↓
Risk Classification
      ↓
SHAP Explainability
      ↓
Findings

This gives XAIDA three independent anomaly perspectives:
Statistical
Cluster-based
Neural-network

For XAIDA, I would implement the ensemble in three modules:
analytics/
├── preprocessing.py
├── autoencoder.py          ← NEW
├── anomaly_detection.py    ← UPDATE
└── analysis_engine.py      ← UPDATE

Final XAIDA Flow
Dataset
    ↓
Preprocessing
    ↓
Feature Engineering
    ↓
Isolation Forest
    ↓
KMeans
    ↓
Autoencoder
    ↓
Weighted Ensemble

        40%
        IF

        20%
        KMeans

        40%
        Autoencoder

    ↓

Risk Score
    ↓

Flagged Transactions
    ↓

SHAP Explainability
    ↓

Findings

For XAIDA, model persistence and reproducibility are essential because auditors must be able to explain:
Why did this transaction get flagged?
Can we reproduce the result?
Which model version was used?
What parameters were applied?

I would add four components.

1. Store Analysis Metadata

Update analysis_engine.py.

After anomaly detection:

analysis_metadata = {

    "model_version":
        "XAIDA-4.0-Ensemble",

    "analysis_date":
        pd.Timestamp.now(),

    "contamination":
        0.05,

    "clusters":
        3,

    "random_seed":
        42,

    "ensemble_weights": {

        "isolation_forest": 0.40,
        "kmeans": 0.20,
        "autoencoder": 0.40,
    },

    "dataset_version":
        session.analysis[
            "dataset_version"
        ],
}

Then return:
"analysis_metadata":
    analysis_metadata,

alongside the other analysis results.

2. Persist Models

Create: analytics/model_registry.py

TensorFlow Autoencoder

Save separately.
autoencoder.save(
    "models/autoencoder.keras"
)

3. Persist Threshold

The most important thing to reproduce anomaly results is: threshold
Store it:

analysis_metadata[
    "threshold"
] = float(
    threshold
)

because flagged transactions are determined by:
ensemble_score >= threshold
Without the threshold, exact reproduction is impossible.

4. Session Reproducibility Artifact

Store everything needed for audit replay.
session.analysis[
    "reproducibility"
] = {

    "model_version":
        "XAIDA-4.0-Ensemble",

    "dataset_version":
        session.analysis[
            "dataset_version"
        ],

    "threshold":
        float(threshold),

    "random_seed":
        42,

    "weights": {

        "isolation": 0.40,

        "kmeans": 0.20,

        "autoencoder": 0.40,
    },

    "feature_count":
        features.shape[1],

    "latent_dimension":
        latent_features.shape[1],
}

5. Persist Feature Names

Very important for SHAP.

Store:
session.analysis[
    "feature_names"
] = feature_names

This lets the auditor see:
Top Risk Drivers

Days_To_Payment
Log_Amount
InvoiceDate_Quarter
Vendor_Global Office

instead of:
Component 1
Component 2
Component 3

6. Add Findings Provenance

Include in Findings:
findings_report = {

    "risk_level":
        risk_level,

    "flagged_transactions":
        len(flagged_transactions),

    "model":
        "IsolationForest + KMeans + Autoencoder",

    "analysis_date":
        analysis_metadata[
            "analysis_date"
        ],
}

Final XAIDA Audit TrailFinal XAIDA Audit Trail
Dataset Version: 3

Preprocessing:
    StandardScaler
    OneHotEncoder
    Date Features

Models:
    Isolation Forest
    KMeans
    Autoencoder

Weights:
    IF = 40%
    KM = 20%
    AE = 40%

Random Seed:
    42

Threshold:
    0.8123

Flagged Transactions:
    37

Risk Level:
    High


This gives XAIDA something very important for audit and research use:

✅ reproducibility
 ✅ model governance
 ✅ explainability traceability
 ✅ repeatable anomaly results
 ✅ report provenance

These are exactly the types of controls auditors and thesis evaluators will ask about when reviewing an explainable AI-based audit platform.

3. Update Autoencoder Persistence

In autoencoder.py:

Python
from tensorflow.keras.models import (
load_model,
)
 
AUTOENCODER_PATH = (
"models/autoencoder.keras"
)
Show more lines

Save:

Python
autoencoder.save(
AUTOENCODER_PATH
)
Show more lines

Load:

Python
autoencoder = load_model(
AUTOENCODER_PATH
)

4. Add Reproducibility Metadata

Inside analysis_engine.py

After anomaly detection:

Python
analysis_metadata = {
 
"model_name":
"XAIDA Ensemble",
 
"model_version":
"4.0",
 
"dataset_version":
session.analysis[
"dataset_version"
],
 
"random_seed":
42,
 
"contamination":
0.05,
 
"cluster_count":
3,
 
"threshold":
float(threshold),
 
"weights": {
 
"isolation_forest": 0.40,
 
"kmeans": 0.20,
 
"autoencoder": 0.40,
},
 
"feature_count":
int(
features.shape[1]
),
 
"latent_dimension":
int(
latent_features.shape[1]
),
}

5. Persist Feature Names

Immediately after preprocessing:

Python
session.analysis[
"feature_names"
] = feature_names

This is critical for SHAP explainability.

6. Persist Complete Results

Before returning from run_analysis():
analysis_result = {

    "analysis_dataframe":
        analysis_df,

    "risk_summary":
        risk_summary,

    "risk_level":
        risk_level,

    "flagged_transactions":
        flagged_transactions,

    "high_risk_transactions":
        high_risk_transactions,

    "top_features":
        top_features,

    "explanations":
        explanations,

    "threshold":
        threshold,

    "analysis_metadata":
        analysis_metadata,
}

Store:

Python
save_analysis_artifact(
analysis_result,
session.analysis[
"dataset_version"
],
)
Show more lines

Then:

Python
session.analysis[
"results"
] = analysis_result
Show more lines

and:

Python
session.analysis[
"analysis_metadata"
] = analysis_metadata

7. Add Audit Trail to Findings

In Findings:

Python
metadata = (
results.get(
"analysis_metadata",
{}
)
)
Show more lines

Display:

Python
st.subheader(
"Analysis Provenance"
)
 
st.json(
metadata
)
Show more lines

Example output:

Plain Text
Model:
XAIDA Ensemble v4.0
 
Weights:
Isolation Forest : 40%
KMeans : 20%
Autoencoder : 40%
 
Dataset Version:
3
 
Random Seed:
42
 
Threshold:
0.8123

Recommended XAIDA Audit Record

Persist this in every analysis:

Python
{
"dataset_version": 3,
"model_version": "XAIDA-4.0",
"random_seed": 42,
"threshold": 0.8123,
"weights": {
"isolation_forest": 0.40,
"kmeans": 0.20,
"autoencoder": 0.40,
},
"feature_names": [...],
"flagged_transactions": ...,
"high_risk_transactions": ...,
}
Show more lines

This gives XAIDA:

✅ Reproducibility
✅ Model governance
✅ Audit traceability
✅ Explainability provenance
✅ Thesis-defensible AI controls
✅ Repeatable anomaly findings across reruns

For XAIDA, adding atomic saves + integrity hashing is an excellent idea because it gives you:

✅ Reproducibility
✅ Audit trail
✅ Tamper detection
✅ Research/thesis defensibility
✅ Model governance

I would update analytics/persistence.py as follows.

analytics/persistence.py
Python
# ============================================================
# XAIDA PERSISTENCE
# Atomic Save + Integrity Hash
# ============================================================
 
import hashlib
import json
import os
import tempfile
from pathlib import Path
 
import joblib
 
ANALYSIS_DIR = Path(
"analysis_artifacts"
)
 
ANALYSIS_DIR.mkdir(
exist_ok=True,
)
 
# ============================================================
# HASHING
# ============================================================
 
def compute_sha256(
filepath,
):
 
sha256 = hashlib.sha256()
 
with open(
filepath,
"rb",
) as file:
 
for chunk in iter(
lambda: file.read(8192),
b"",
):
 
sha256.update(
chunk
)
 
return sha256.hexdigest()
 
 
# ============================================================
# ATOMIC SAVE
# ============================================================
 
def atomic_joblib_dump(
obj,
filepath,
):
 
filepath = Path(
filepath
)
 
with tempfile.NamedTemporaryFile(
delete=False,
dir=filepath.parent,
suffix=".tmp",
) as tmp:
 
temp_path = Path(
tmp.name
)
 
try:
 
joblib.dump(
obj,
temp_path,
)
 
os.replace(
temp_path,
filepath,
)
 
finally:
 
if temp_path.exists():
 
temp_path.unlink(
missing_ok=True
)
 
 
# ============================================================
# SAVE ANALYSIS ARTIFACT
# ============================================================
 
def save_analysis_artifact(
analysis_result,
dataset_version,
):
 
artifact_path = (
ANALYSIS_DIR
/
f"analysis_v{dataset_version}.joblib"
)
 
atomic_joblib_dump(
analysis_result,
artifact_path,
)
 
sha256_hash = (
compute_sha256(
artifact_path
)
)
 
metadata = {
 
"dataset_version":
dataset_version,
 
"artifact_file":
artifact_path.name,
 
"sha256":
sha256_hash,
}
 
metadata_path = (
ANALYSIS_DIR
/
f"analysis_v{dataset_version}.json"
)
 
with open(
metadata_path,
"w",
encoding="utf-8",
) as file:
 
json.dump(
metadata,
file,
indent=4,
)
 
return {
 
"artifact":
str(
artifact_path
),
 
"metadata":
str(
metadata_path
),
 
"sha256":
sha256_hash,
}
 
 
# ============================================================
# LOAD ANALYSIS ARTIFACT
# ============================================================
 
def load_analysis_artifact(
dataset_version,
):
 
artifact_path = (
ANALYSIS_DIR
/
f"analysis_v{dataset_version}.joblib"
)
 
metadata_path = (
ANALYSIS_DIR
/
f"analysis_v{dataset_version}.json"
)
 
with open(
metadata_path,
"r",
encoding="utf-8",
) as file:
 
metadata = json.load(
file
)
 
current_hash = (
compute_sha256(
artifact_path
)
)
 
if (
current_hash
!=
metadata["sha256"]
):
 
raise ValueError(
"Artifact integrity check failed."
)
 
return joblib.load(
artifact_path
)
Show more lines
Update analysis_engine.py

After creating analysis_result:

Python
from analytics.persistence import (
save_analysis_artifact,
)
Show more lines

Then:

Python
artifact_info = (
save_analysis_artifact(
analysis_result,
session.analysis[
"dataset_version"
],
)
)
Show more lines

Store:

Python
analysis_result[
"artifact_info"
] = artifact_info
Show more lines
Add Dataset Integrity Hash

I strongly recommend adding this too.

Before running the analysis:

Python
dataset_hash = hashlib.sha256(
 
dataframe.to_csv(
index=False
).encode()
 
).hexdigest()
Show more lines

Store it inside metadata:

Python
analysis_metadata[
"dataset_hash"
] = dataset_hash
Show more lines

This allows XAIDA to prove:

Plain Text
Dataset Version ........ 5
 
Dataset Hash ........... 7f8b2...
 
Model Version .......... XAIDA-4.0
 
Analysis Threshold ..... 0.8123
 
 
Show more lines
Expected Audit Output

In Findings → Analysis Provenance:

JSON
{
"model_version": "XAIDA-4.0-Ensemble",
"dataset_version": 3,
"dataset_hash": "a817a6...",
"threshold": 0.8123,
"random_seed": 42,
"weights": {
"isolation_forest": 0.40,
"kmeans": 0.20,
"autoencoder": 0.40
},
"artifact_sha256": "c433a9..."
}
Show more lines

This gives XAIDA tamper-evident analysis artefacts and fully reproducible anomaly-detection results, which is exactly the kind of control expected in audit analytics platforms.

What I Recommend For XAIDA

For XAIDA 4.0, keep both:

Python
transform_features()
reduce_dimensions()
Show more lines

inside preprocessing.py.

Even if you're using Autoencoder.

Why?

This lets you support:

Plain Text
FAST MODE
PCA + Isolation Forest + KMeans
 
ADVANCED MODE
Autoencoder + Isolation Forest + KMeans
 
RESEARCH MODE
PCA + Autoencoder + Isolation Forest + KMeans
Show more lines

without breaking existing imports.


At this point, the core analytics engine is already quite mature.

Priority 1: Editable Dataset + Change Tracking

This should be next.

Why?

You already have:

Plain Text
Audit Trail
Dataset Versioning
Show more lines

but not:

Plain Text
WHO changed WHAT?
Show more lines

Add:

Python
st.data_editor()
Show more lines

to:

Plain Text
Original Dataset
Analysis Dataset
Show more lines

Then capture:

Python
Row
Column
Old Value
New Value
Timestamp
Show more lines

Example audit log entry:

Python
{
"stage": "Dataset Editing",
"action": "Cell Updated",
"row": 115,
"column": "Vendor",
"old_value": "ABC Supply",
"new_value": "ABC Supplies",
}
Show more lines

This becomes the basis of:

Plain Text
Dataset Modification Log
Show more lines

in the report.

Priority 2: Evidence Panel Enhancement

Keep charts AND dataframes.

Recommended sections:

Plain Text
Dataset Overview
Show more lines
Plain Text
Audit Trail
Show more lines
Plain Text
Analysis Results
Show more lines
Plain Text
Visualisations
Show more lines
Plain Text
Findings
Show more lines
Plain Text
Explainability
Show more lines
Plain Text
Model Provenance
Show more lines
Plain Text
Dataset History
Show more lines
Priority 3: Report Generation

Only do this after edit tracking.

Otherwise your report cannot answer:

Plain Text
What rows were modified?
Show more lines

or

Plain Text
What changed between upload and analysis?
Show more lines

Recommended outputs:

PDF

Management Report

DOCX

Working Papers

XLSX

Detailed Findings

Priority 4: Dataset History Table

Create:

Python
session.dataset_history
Show more lines

Example:

Version	Event	Records1	Upload	809
2	Duplicate Removal	799
3	Manual Edit	799

This will drive:

Evidence Panel
Audit Trail
PDF Reports
Priority 5: Auditor Workflow

Add reviewer fields:

Python
Reviewer
Review Date
Disposition
Notes
Status
Show more lines

to:

Python
flagged_transactions
Show more lines

Example:

APID	Risk	DispositionAP10025	High	Confirmed Anomaly
AP10026	Medium	False Positive

This dramatically increases audit usefulness.



1. Versioned Dataset Snapshots ⭐ Highest Priority

Right now you correctly track:

Plain Text
V1 Dataset Loaded
V2 Imputation Applied
V3 Duplicate Removal
V4 Analysis Dataset Generated
V5 Explainability Dataset Generated
Show more lines

But XAIDA cannot yet reconstruct those versions.

Add:

Python
session.analysis[
"dataset_versions"
]
Show more lines

Example:

Python
session.analysis[
"dataset_versions"
] = {
1: original_dataframe.copy(),
2: imputed_dataframe.copy(),
3: deduplicated_dataframe.copy(),
4: analysis_dataframe.copy(),
5: explainability_dataframe.copy(),
}
Show more lines

This transforms audit logging into true lineage.

Auditor benefit:

Plain Text
Show me Version 2
Show more lines

and XAIDA can actually display it.

2. Persist SHAP Results Into Dataset ⭐

You already incremented version after:

Plain Text
Explainability Dataset Generated
Show more lines

But make sure the dataset truly changes.

Example:

Python
analysis_df["Risk Score"]
 
analysis_df["Anomaly Flag"]
 
analysis_df["Primary Driver"]
 
analysis_df["Explanation"]
Show more lines

If those columns are not yet being physically added to the dataframe, Version 5 is not a real dataset revision.

3. Trace Dataset Modifications

You already started using:

Python
st.data_editor()
Show more lines

Eventually you'll want:

Plain Text
Dataset Editing
Cell Updated
 
Version 6
Show more lines

Audit example:

Plain Text
Dataset Editing
Cell Updated
 
Row: 134
Column: Amount
 
Old Value: 1500
New Value: 15000
Show more lines

This is probably your next major governance feature.

4. Evidence-Based PDF Report

Your audit trail is now strong enough to drive report generation.

Sections:

Plain Text
Executive Summary
 
Dataset Profile
 
Data Preparation Summary
 
Duplicate Review Summary
 
Analysis Summary
 
Explainability Summary
 
Dataset Lineage
 
Audit Trail
Show more lines

Include:

Plain Text
Dataset Versions
 
Show more lines

in the report.

5. Lineage Panel

New Evidence Panel section:

Plain Text
Dataset Lineage
Show more lines

Example:

Version	EventV1	Dataset Loaded
V2	Imputation Applied
V3	Duplicate Copies Removed
V4	Analysis Attributes Added
V5	SHAP Explanations Added

Clicking a version could show the snapshot.

6. Re-analysis Detection

You already have:

Python
analysis_version
dataset_version
`
Show more lines

Use them fully.

If:

Python
dataset_version > analysis_version
Show more lines

display:

Plain Text
Analysis Outdated
 
Dataset changed after analysis.
Re-run analysis required.
Show more lines

This is a very valuable governance control.

If this were my XAIDA roadmap, I'd do:

Plain Text
1. Dataset Snapshots
2. Dataset Editing Audit Trail
3. Lineage Panel
4. PDF Report Enhancement
5. Re-analysis Detection
Show more lines

Those five features would move XAIDA from a working prototype into a genuinely auditable analytics platform.