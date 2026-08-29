from pathlib import Path
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "etl_output"


# ============================================================
# LOAD ALL CSV FILES
# ============================================================

print("\n" + "=" * 70)
print("LOADING FINAL DATASET FOR VALIDATION")
print("=" * 70)


def load_csv(filename):
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    return pd.read_csv(path, encoding="utf-8-sig")


division = load_csv("division.csv")
district = load_csv("district.csv")
city = load_csv("city.csv")
owner = load_csv("owner.csv")
category = load_csv("category.csv")
museum = load_csv("museum.csv")
gallery = load_csv("gallery.csv")
artifact_type = load_csv("artifact_type.csv")
material = load_csv("material.csv")
dimension = load_csv("dimension.csv")
artifact = load_csv("artifact.csv")
image = load_csv("image.csv")
entry_fee = load_csv("entry_fee.csv")
opening_hours = load_csv("opening_hours.csv")
closed_days = load_csv("closed_days.csv")
contact = load_csv("contact.csv")
source = load_csv("source.csv")


# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

errors = []
warnings = []


def check_primary_key(df, table_name, pk):

    null_count = df[pk].isna().sum()
    duplicate_count = df[pk].duplicated().sum()

    if null_count > 0:
        errors.append(
            f"{table_name}: {null_count} NULL value(s) in primary key {pk}"
        )

    if duplicate_count > 0:
        errors.append(
            f"{table_name}: {duplicate_count} duplicate value(s) in primary key {pk}"
        )

    if null_count == 0 and duplicate_count == 0:
        print(f"✅ {table_name:20} PK {pk} is valid")


def check_fk(
    child_df,
    child_table,
    fk_col,
    parent_df,
    parent_table,
    parent_pk
):

    invalid = child_df[
        child_df[fk_col].notna()
        &
        ~child_df[fk_col].isin(parent_df[parent_pk])
    ]

    null_count = child_df[fk_col].isna().sum()

    if len(invalid) > 0:

        errors.append(
            f"{child_table}.{fk_col}: "
            f"{len(invalid)} invalid FK value(s), "
            f"not found in {parent_table}.{parent_pk}"
        )

        print(
            f"❌ {child_table:20} {fk_col} "
            f"-> {parent_table}.{parent_pk} "
            f"| INVALID = {len(invalid)}"
        )

    else:

        print(
            f"✅ {child_table:20} {fk_col} "
            f"-> {parent_table}.{parent_pk} "
            f"| valid"
        )

    if null_count > 0:

        warnings.append(
            f"{child_table}.{fk_col}: "
            f"{null_count} NULL value(s)"
        )


def check_duplicate_combination(
    df,
    table_name,
    columns
):

    duplicate_count = df.duplicated(
        subset=columns
    ).sum()

    if duplicate_count > 0:

        warnings.append(
            f"{table_name}: "
            f"{duplicate_count} duplicate combination(s) "
            f"in {columns}"
        )

        print(
            f"⚠️ {table_name:20} "
            f"duplicate combinations = {duplicate_count}"
        )

    else:

        print(
            f"✅ {table_name:20} "
            f"no duplicate combinations"
        )


# ============================================================
# 1. PRIMARY KEY VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("1. PRIMARY KEY VALIDATION")
print("=" * 70)


check_primary_key(
    division,
    "DIVISION",
    "Division_ID"
)

check_primary_key(
    district,
    "DISTRICT",
    "District_ID"
)

check_primary_key(
    city,
    "CITY",
    "City_ID"
)

check_primary_key(
    owner,
    "OWNER",
    "Owner_ID"
)

check_primary_key(
    category,
    "CATEGORY",
    "Category_ID"
)

check_primary_key(
    museum,
    "MUSEUM",
    "Museum_ID"
)

check_primary_key(
    artifact_type,
    "ARTIFACT_TYPE",
    "Artifact_Type_ID"
)

check_primary_key(
    material,
    "MATERIAL",
    "Material_ID"
)

check_primary_key(
    dimension,
    "DIMENSION",
    "Dimension_ID"
)

check_primary_key(
    artifact,
    "ARTIFACT",
    "Artifact_ID"
)


# ============================================================
# 2. FOREIGN KEY VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("2. FOREIGN KEY VALIDATION")
print("=" * 70)


check_fk(
    district,
    "DISTRICT",
    "Division_ID",
    division,
    "DIVISION",
    "Division_ID"
)

check_fk(
    city,
    "CITY",
    "District_ID",
    district,
    "DISTRICT",
    "District_ID"
)

check_fk(
    museum,
    "MUSEUM",
    "City_ID",
    city,
    "CITY",
    "City_ID"
)

check_fk(
    museum,
    "MUSEUM",
    "Owner_ID",
    owner,
    "OWNER",
    "Owner_ID"
)

check_fk(
    museum,
    "MUSEUM",
    "Category_ID",
    category,
    "CATEGORY",
    "Category_ID"
)

check_fk(
    gallery,
    "GALLERY",
    "Museum_ID",
    museum,
    "MUSEUM",
    "Museum_ID"
)

check_fk(
    artifact,
    "ARTIFACT",
    "Museum_ID",
    museum,
    "MUSEUM",
    "Museum_ID"
)

check_fk(
    artifact,
    "ARTIFACT",
    "Artifact_Type_ID",
    artifact_type,
    "ARTIFACT_TYPE",
    "Artifact_Type_ID"
)

check_fk(
    artifact,
    "ARTIFACT",
    "Material_ID",
    material,
    "MATERIAL",
    "Material_ID"
)

check_fk(
    artifact,
    "ARTIFACT",
    "Dimension_ID",
    dimension,
    "DIMENSION",
    "Dimension_ID"
)

check_fk(
    image,
    "IMAGE",
    "Artifact_ID",
    artifact,
    "ARTIFACT",
    "Artifact_ID"
)

check_fk(
    entry_fee,
    "ENTRY_FEE",
    "Museum_ID",
    museum,
    "MUSEUM",
    "Museum_ID"
)

check_fk(
    opening_hours,
    "OPENING_HOURS",
    "Museum_ID",
    museum,
    "MUSEUM",
    "Museum_ID"
)

check_fk(
    closed_days,
    "CLOSED_DAYS",
    "Museum_ID",
    museum,
    "MUSEUM",
    "Museum_ID"
)

check_fk(
    contact,
    "CONTACT",
    "Museum_ID",
    museum,
    "MUSEUM",
    "Museum_ID"
)

check_fk(
    source,
    "SOURCE",
    "Museum_ID",
    museum,
    "MUSEUM",
    "Museum_ID"
)


# ============================================================
# 3. DUPLICATE CHECK
# ============================================================

print("\n" + "=" * 70)
print("3. DUPLICATE DATA CHECK")
print("=" * 70)


check_duplicate_combination(
    gallery,
    "GALLERY",
    ["Museum_ID", "Gallery_No"]
)

check_duplicate_combination(
    image,
    "IMAGE",
    ["Artifact_ID", "Image_URL"]
)

check_duplicate_combination(
    entry_fee,
    "ENTRY_FEE",
    ["Museum_ID", "Fee_Type"]
)

check_duplicate_combination(
    source,
    "SOURCE",
    ["Museum_ID", "Source_Link"]
)

check_duplicate_combination(
    closed_days,
    "CLOSED_DAYS",
    ["Museum_ID", "Closed_Day_Name"]
)


# ============================================================
# 4. NULL CHECK FOR IMPORTANT COLUMNS
# ============================================================

print("\n" + "=" * 70)
print("4. IMPORTANT NULL VALUE CHECK")
print("=" * 70)


important_checks = {

    "MUSEUM.Museum_Name":
    museum["Museum_Name"],

    "ARTIFACT.Artifact_Name":
    artifact["Artifact_Name"],

    "ARTIFACT.Museum_ID":
    artifact["Museum_ID"],

    "ARTIFACT.Artifact_Type_ID":
    artifact["Artifact_Type_ID"],

    "ARTIFACT.Material_ID":
    artifact["Material_ID"],

    "SOURCE.Museum_ID":
    source["Museum_ID"],

    "SOURCE.Source_Link":
    source["Source_Link"]
}


for name, column in important_checks.items():

    null_count = column.isna().sum()

    print(
        f"{name:30} NULL = {null_count}"
    )


# ============================================================
# 5. MUSEUM NAME DUPLICATE CHECK
# ============================================================

print("\n" + "=" * 70)
print("5. MUSEUM NAME DUPLICATE CHECK")
print("=" * 70)


duplicate_museum_names = museum[
    museum["Museum_Name"].duplicated(
        keep=False
    )
]


if duplicate_museum_names.empty:

    print(
        "✅ No duplicate Museum_Name found"
    )

else:

    warnings.append(
        f"MUSEUM: "
        f"{len(duplicate_museum_names)} rows "
        f"have duplicate museum names"
    )

    print(
        "⚠️ Duplicate Museum_Name found:"
    )

    print(
        duplicate_museum_names[
            [
                "Museum_ID",
                "Museum_Name"
            ]
        ]
    )


# ============================================================
# 6. FINAL REPORT
# ============================================================

print("\n" + "=" * 70)
print("FINAL VALIDATION REPORT")
print("=" * 70)


print("\nTOTAL ERRORS:", len(errors))

if len(errors) == 0:

    print(
        "🎉 NO REFERENTIAL INTEGRITY ERRORS FOUND"
    )

else:

    print("\nERRORS:")

    for error in errors:

        print("❌", error)


print("\nTOTAL WARNINGS:", len(warnings))

if len(warnings) > 0:

    print("\nWARNINGS:")

    for warning in warnings:

        print("⚠️", warning)

else:

    print(
        "🎉 NO WARNINGS FOUND"
    )


print("\n" + "=" * 70)

if len(errors) == 0:

    print(
        "DATASET VALIDATION PASSED ✅"
    )

    print(
        "Dataset is ready for the next database implementation step."
    )

else:

    print(
        "DATASET VALIDATION FAILED ❌"
    )

    print(
        "Fix the errors before importing into MySQL."
    )

print("=" * 70)