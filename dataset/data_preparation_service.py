from core.validation import (
    validate_dataset,
    generate_dataset_profile,
)

from dataset.missing_value_service import (
    profile_missing_values,
    classify_missing_values,
    prepare_dataset_for_analysis,
)
from dataset.imputation_rules import DEFAULT_IMPUTATION_RULES

from dataset.duplicate_detection import (
    detect_duplicates,
)

from audit.audit_logger import (
    log_audit_event,
)

from dataset.version_manager import (
    create_dataset_version,
)

from audit.services.audit_readiness import (
    calculate_audit_readiness,
)

def run_data_preparation(session):

    dataframe = (
        session.dataset.get(
            "dataframe"
        )
    )

    if dataframe is None:
        raise ValueError(
            "No dataset loaded."
        )

    session.dataset["data_preparation_complete"] = False
    
    if (
        "dataset_versions"
        not in session.analysis
    ):

        session.analysis[
            "dataset_versions"
        ] = {}

    if (
        1
        not in session.analysis[
            "dataset_versions"
        ]
    ):

        session.analysis[
            "dataset_versions"
        ][1] = dataframe.copy()
        
    profile = (
        generate_dataset_profile(
            dataframe
        )
    )

    missing_summary = (
        profile_missing_values(
            dataframe
        )
    )

    missing_classification = (
        classify_missing_values(
            dataframe
        )
    )

# =====================================
# MISSING VALUE CLASSIFICATION METRICS
# =====================================

    total_records = len(dataframe)

    unexpected_records = sum(
        item["records"]
        for item in
        missing_classification.get(
            "unexpected",
            []
        )
    )

    unexpected_missing_percentage = (
        round(
            (
                unexpected_records
                / total_records
            ) * 100,
            2,
        )
        if total_records > 0
        else 0
    )

    # =====================================
    # VALIDATION
    # =====================================

    validation = (
        validate_dataset(
            dataframe
        )
    )
    session.dataset["validation_status"] = (
        "Completed" if validation.get("valid") else "Failed"
    )
    session.dataset["validation_results"] = validation

    # =====================================
    # DUPLICATE DETECTION
    # =====================================

    duplicates = (
        detect_duplicates(
            dataframe
        )
    )
        
    duplicate_groups = 0

    if (
        duplicates is not None
        and
        not duplicates.empty
        and
        "Duplicate Group"
        in duplicates.columns
    ):
        duplicate_groups = (
            duplicates[
                "Duplicate Group"
            ].nunique()
        )

    (
        prepared_dataframe,
        treatment_log,
    ) = (
        prepare_dataset_for_analysis(
            dataframe
        )
    )

    session.dataset[
        "profile"
    ] = profile

    session.dataset[
        "missing_summary"
    ] = missing_summary

    session.dataset[
        "missing_classification"
    ] = (
        missing_classification
    )

    session.dataset[
        "unexpected_missing_percentage"
    ] = unexpected_missing_percentage

    session.dataset[
        "prepared_dataframe"
    ] = prepared_dataframe

    session.dataset[
        "imputation_log"
    ] = treatment_log

    session.dataset[
        "imputation_rules"
    ] = DEFAULT_IMPUTATION_RULES

    modifying_treatments = [
        treatment
        for treatment in treatment_log
        if treatment.get(
            "strategy"
        ) not in [
            "retain",
        ]
    ]

    if modifying_treatments:

        current_version = (
            create_dataset_version(
                session=session,
                dataframe=prepared_dataframe,
                stage="Data Preparation",
                action="Imputation Applied",
                metadata={
                    "imputation_count":
                        len(
                            modifying_treatments
                        ),
                },
            )
        )

        log_audit_event(
            session,
            stage="Data Preparation",
            action="Imputation Applied",
            details=(
                f"{len(modifying_treatments)} "
                "imputation rules applied"
            ),
        )

    elif treatment_log:

        log_audit_event(
            session,
            stage="Data Preparation",
            action="Null Values Retained",
            details=(
                "Business-valid null values "
                "retained. No dataset "
                "modifications were applied."
            ),
        )

    session.duplicates[
        "duplicate_count"
    ] = len(
        duplicates
    )

    session.duplicates[
        "duplicate_groups"
    ] = duplicate_groups

    session.duplicates[
        "duplicate_records"
    ] = duplicates

    session.analysis[
        "audit_readiness"
    ] = (
        calculate_audit_readiness(
            session
        )
    )

    session.dataset["data_preparation_complete"] = True

    print(
        session.analysis[
            "audit_readiness"
        ]
    )

    return {
        "validation": validation,
        "duplicates": duplicates,
    }