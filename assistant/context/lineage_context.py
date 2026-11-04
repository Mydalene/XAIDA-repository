from audit.change_tracker import get_change_log


# ===================================
# DATASET LINEAGE
# ===================================

def build_lineage_context(
    session,
):

    version_metadata = (
        session.analysis.get(
            "dataset_version_metadata",
            {},
        )
    )
    versions = session.analysis.get("dataset_versions", {}) or {}
    version_history = []
    for version, dataframe in versions.items():
        metadata = (
            version_metadata.get(version)
            or version_metadata.get(str(version))
            or {}
        )
        version_history.append(
            {
                "version": version,
                "version_label": f"V{version}",
                "stage": metadata.get("stage"),
                "action": metadata.get("action"),
                "dataset_type": metadata.get("dataset_type"),
                "records": len(dataframe) if dataframe is not None else None,
                "columns": (
                    len(dataframe.columns)
                    if dataframe is not None
                    else None
                ),
            }
        )

    removed_duplicates = (
        session.duplicates.get(
            "removed_duplicate_records"
        )
    )

    return {

        # ==========================
        # VERSIONS
        # ==========================

        "dataset_versions":
            len(versions),

        "dataset_version_history":
            version_history,

        "dataset_versions_downloadable":
            any(dataframe is not None for dataframe in versions.values()),

        "dataset_version_download_format":
            "CSV",

        "dataset_version_download_location":
            "Lineage evidence tab: select a dataset version and use its CSV download button.",

        # ==========================
        # LINEAGE
        # ==========================

        "dataset_lineage_summary":
        (
            session.dataset.get(
                "dataset_lineage_summary"
            )
        ),

        # ==========================
        # CHANGE HISTORY
        # ==========================

        "dataset_change_history":
            get_change_log(session),

        # ==========================
        # DUPLICATE REMOVAL
        # ==========================

        "removed_duplicate_count":
        (
            len(
                removed_duplicates
            )
            if removed_duplicates
            is not None
            else 0
        ),

        "removed_duplicate_records":
        {
            "available": removed_duplicates is not None,
            "record_count": (
                len(removed_duplicates)
                if removed_duplicates is not None
                else 0
            ),
            "columns": (
                list(removed_duplicates.columns)
                if removed_duplicates is not None
                else []
            ),
        },

        "removed_duplicate_record_sample":
        (
            removed_duplicates.to_dict("records")
            if removed_duplicates is not None
            else []
        ),

        "duplicate_removal_schedule":
            session.duplicates.get("duplicate_removal_schedule", []),

        "duplicate_removal_strategy":
        (
            session.duplicates.get(
                "strategy"
            )
        ),

        # ==========================
        # NAVIGATION
        # ==========================

        "lineage_sections":
        [
            "Dataset Lineage",
            "Dataset Versions",
            "Change History",
            "Removed Duplicate Records",
        ],

        "lineage_workflow_steps":
        [
            "Review Dataset Versions",
            "Review Version Metadata",
            "Review Change History",
            "Review Removed Duplicates",
            "Review Dataset Evolution",
        ],
    }