from dataset.sample_dataset_loader import SAMPLE_DATASETS


def build_platform_help_context():
    return {
        "dataset_upload_requirements": {
            "accepted_formats": [".csv", ".xlsx"],
            "requirements": [
                "The file must contain at least one data row and one column.",
                "The first row is read as the column header.",
            ],
        },
        "dataset_upload_location": (
            "Upload a dataset using the upload control in the left-side panel. "
            "The Dataset evidence tab displays the loaded dataset; it is not "
            "the upload location."
        ),
        "sample_dataset_catalog": list(SAMPLE_DATASETS),
        "evidence_tab_contents": {
            "Lineage": [
                "Dataset versions",
                "CSV download for each selected dataset version",
                "Dataset change history",
                "Removed duplicate artifact details",
            ],
            "Findings": [
                "Findings register and status metrics",
                "Source and findings dataset versions",
            ],
        },
        "platform_navigation_help": {
            "evidence_tabs": [
                "Dataset",
                "Data Processing",
                "Duplicate Review",
                "Anomaly Detection",
                "Explainability",
                "Audit Review",
                "Findings",
                "Reports",
                "Lineage",
                "Audit Trail",
            ],
            "navigation": (
                "Use the evidence tabs in the main workspace to inspect "
                "audit data. Workflow actions are available in the sidebar "
                "and change as the audit progresses."
            ),
            "workflow_stages": [
                "Initialization",
                "Dataset",
                "Data Preparation",
                "Duplicate Review",
                "Analysis",
                "Explainability",
                "Audit Review",
                "Findings",
                "Reporting",
                "Audit Completion",
            ],
        },
    }
