import pandas as pd

from audit.audit_logger import (
    log_audit_event,
)
from dataset.version_manager import (
    create_dataset_version,
)

from audit.services.audit_readiness import (
    calculate_audit_readiness,
)

def retain_all_duplicates(
    session
):
    dataframe = (
        session.dataset[
            "dataframe"
        ]
    )

    session.duplicates[
        "strategy"
    ] = "retain_all"

    session.duplicates[
        "duplicate_review_complete"
    ] = True

    session.analysis[
        "analysis_dataset"
    ] = dataframe.copy()

    session.analysis[
        "analysis_dataset_summary"
    ] = {
        "original_records":
            len(dataframe),
        "records_removed":
            0,
        "records_retained":
            len(dataframe),
        "strategy":
            "retain_all",
    }

    session.analysis[
        "analysis_required"
    ] = True

    log_audit_event(

        session,

        stage="Duplicate Review",

        action="Retain All Duplicates",

        details=(
            f"{len(dataframe)} "
            "records retained"
        ),
    )
    
def remove_duplicate_copies(
    session
):
    original_df = (
        session.dataset[
            "dataframe"
        ]
    )

#
# Identify removed duplicates
#

    removed_duplicates = (
        original_df[
            original_df.duplicated(
                keep="first"
            )
        ]
        .copy()
    )

    removal_schedule = []
    duplicate_positions = (
        original_df.duplicated(keep=False)
        .to_numpy()
        .nonzero()[0]
        .tolist()
    )
    duplicate_frame = original_df.iloc[duplicate_positions]
    duplicate_groups = duplicate_frame.groupby(
        list(original_df.columns),
        dropna=False,
        sort=True,
    ).indices
    for duplicate_group, positions in enumerate(
        duplicate_groups.values(),
        start=1,
    ):
        if len(positions) < 2:
            continue
        retained_position = duplicate_positions[int(positions[0])]
        for removed_position in positions[1:]:
            removed_position = duplicate_positions[int(removed_position)]
            removal_schedule.append(
                {
                    "duplicate_group": duplicate_group,
                    "retained_source_row_position": retained_position + 1,
                    "removed_source_row_position": removed_position + 1,
                    "retained_source_index": original_df.index[
                        retained_position
                    ],
                    "removed_source_index": original_df.index[
                        removed_position
                    ],
                    "retained_record": original_df.iloc[
                        retained_position
                    ].to_dict(),
                    "removed_record": original_df.iloc[
                        removed_position
                    ].to_dict(),
                }
            )

    session.duplicates["duplicate_removal_schedule"] = removal_schedule

    clean_df = (
        original_df
        .drop_duplicates(
            keep="first"
        )
    )

    records_removed = (
        len(original_df)
        - len(clean_df)
    )

    session.duplicates[
        "removed_duplicate_records"
    ] = (
        removed_duplicates
    )

    session.duplicates[
        "removed_duplicate_count"
    ] = (
        len(
            removed_duplicates
        )
    )

    # =====================================
    # DUPLICATE REVIEW STATUS
    # =====================================

    session.duplicates[
        "strategy"
    ] = "retain_first"

    session.duplicates[
        "duplicate_review_complete"
    ] = True

    session.analysis[
        "analysis_required"
    ] = True

    # =====================================
    # VERSIONING
    # =====================================

    new_version = (
        create_dataset_version(
            session=session,
            dataframe=clean_df,
            stage="Duplicate Review",
            action="Remove Duplicate Copies",
            metadata={
                "records_removed":
                    records_removed,
            },
        )
    )


    # =====================================
    # ANALYSIS DATASET
    # =====================================

    session.analysis[
        "analysis_dataset"
    ] = clean_df.copy()

    # =====================================
    # SUMMARY
    # =====================================

    session.analysis[
        "analysis_dataset_summary"
    ] = {
        "original_records":
            len(original_df),
        "records_retained":
            len(clean_df),
        "records_removed":
            records_removed,
        "strategy":
            "retain_first",
    }

    # =====================================
    # DUPLICATE METRICS
    # =====================================

    session.duplicates[
        "records_removed"
    ] = records_removed

    log_audit_event(
        session,
        stage="Duplicate Review",
        action="Remove Duplicate Copies",
        details=(
            f"{records_removed} duplicate "
            f"records removed and "
            f"preserved for evidence."
        ),
    )


def remove_rows(
    session,
    indices,
):
    current_df = (
        session.analysis.get(
            "analysis_dataset"
        )
    )

    if current_df is None:
        current_df = (
            session.dataset.get(
                "dataframe"
            )
        )

    if current_df is None:
        raise ValueError(
            "No dataset available."
        )

    # =====================================
    # REMOVE ROWS
    # =====================================

    original_record_count = len(
        current_df
    )

    removed_records = (
        current_df.loc[
            indices
        ]
        .copy()
    )

    existing_removed = (
        session.duplicates.get(
            "removed_duplicate_records"
        )
    )

    if (
        existing_removed is not None
        and
        not existing_removed.empty
    ):

        removed_records = pd.concat(
            [
                existing_removed,
                removed_records,
            ],
            ignore_index=False,
        )

    session.duplicates[
        "removed_duplicate_records"
    ] = removed_records

    updated_df = (
        current_df.drop(
            indices
        )
    )

    # =====================================
    # AUDIT READINESS
    # =====================================

    session.analysis[
        "audit_readiness"
    ] = (
        calculate_audit_readiness(
            session
        )
    )

    # =====================================
    # DATASET VERSIONING
    # =====================================

    new_version = (
        create_dataset_version(
            session=session,
            dataframe=updated_df,
            stage="Duplicate Review",
            action="Manual Duplicate Removal",
            metadata={
                "records_removed":
                    len(indices),
            },
        )
    )

    # =====================================
    # UPDATE ACTIVE DATASETS
    # =====================================

    session.analysis[
        "analysis_dataset"
    ] = (
        updated_df.copy()
    )

    session.dataset[
        "dataframe"
    ] = (
        updated_df.copy()
    )

    # =====================================
    # UPDATE DUPLICATE DATASET
    # =====================================

    duplicates = (
        session.duplicates.get(
            "duplicate_records"
        )
    )

    if duplicates is not None:

        updated_duplicates = (
            duplicates.drop(
                indices
            )
        )

        session.duplicates[
            "duplicate_records"
        ] = updated_duplicates

        session.duplicates[
            "duplicate_count"
        ] = len(
            updated_duplicates
        )

        if (
            "Duplicate Group"
            in updated_duplicates.columns
        ):

            remaining_groups = (
                updated_duplicates
                .groupby(
                    "Duplicate Group"
                )
                .size()
            )

            session.duplicates[
                "duplicate_groups"
            ] = int(
                (
                    remaining_groups > 1
                ).sum()
            )

    # =====================================
    # UPDATE SUMMARY
    # =====================================
    summary = (
        session.analysis.get(
            "analysis_dataset_summary",
            {}
        )
    )
    
    session.analysis[
        "analysis_dataset_summary"
    ] = {
        "original_records":
            original_record_count,

        "records_removed":
            len(indices),

        "records_retained":
            len(updated_df),

        "strategy":
            "manual_duplicate_review",
    }
    
    # =====================================
    # AUDIT LOG
    # =====================================

    log_audit_event(
        session,
        stage="Duplicate Review",
        action=
            "Manual Duplicate Removal",
        details=(
            f"Removed duplicate records: "
            f"{list(indices)}"
            f"records removed and "
            f"preserved for evidence."
        ),
    )

    # =====================================
    # RETURN RESULT
    # =====================================

    return {
        "updated_df":
            updated_df,
        "version":
            new_version,
        "records_removed":
            len(indices),
    }
