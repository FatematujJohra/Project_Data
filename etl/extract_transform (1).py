
from pathlib import Path
import pandas as pd
import numpy as np
import re
import shutil

INPUT_FILE = Path("Data/all_data.xlsx")
OUTPUT_DIR = Path("etl_output")

def clean_text(x):
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s.lower() in {"", "nan", "none", "null", "n/a", "na", "-"}:
        return pd.NA
    s = re.sub(r"\s+", " ", s)
    return s

def clean_series(s):
    return s.map(clean_text)

def key_text(x):
    x = clean_text(x)
    if pd.isna(x):
        return pd.NA
    return str(x).casefold()

def make_lookup(values, id_col, value_col):
    vals = clean_series(values).dropna()
    temp = pd.DataFrame({value_col: vals})
    temp["_key"] = temp[value_col].map(key_text)
    temp = temp.drop_duplicates("_key").sort_values(value_col, key=lambda x: x.str.casefold()).reset_index(drop=True)
    temp[id_col] = range(1, len(temp) + 1)
    return temp[[id_col, value_col]]

def map_id(value, lookup, value_col, id_col):
    if pd.isna(value):
        return pd.NA
    d = dict(zip(lookup[value_col].map(key_text), lookup[id_col]))
    return d.get(key_text(value), pd.NA)

def parse_coord(s):
    # Keep original coordinates because ER has one Coordinates attribute.
    return clean_text(s)

def parse_dimension(s):
    s = clean_text(s)
    if pd.isna(s):
        return pd.Series([pd.NA, pd.NA, pd.NA])
    t = str(s).lower().replace("×", "x")
    nums = re.findall(r"(?<!\w)(\d+(?:\.\d+)?)\s*(cm|mm|m)?", t)
    # only trust common "a x b x c" / "a x b" patterns
    if "x" in t and len(nums) in (2, 3):
        vals = [f"{n} {u}".strip() for n, u in nums[:3]]
        vals += [pd.NA] * (3-len(vals))
        return pd.Series(vals[:3])
    m = re.search(r"(?:height|high)\s*[:~]?\s*(\d+(?:\.\d+)?\s*(?:cm|mm|m)?)", t)
    if m:
        return pd.Series([pd.NA, pd.NA, m.group(1)])
    return pd.Series([pd.NA, pd.NA, pd.NA])

def split_closed_days(s):
    s = clean_text(s)
    if pd.isna(s):
        return []
    parts = re.split(r"[;,/]+", str(s))
    return [clean_text(p) for p in parts if not pd.isna(clean_text(p))]

# ---------- 1. Load ----------
if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Cannot find: {INPUT_FILE.resolve()}")

museum_raw = pd.read_excel(INPUT_FILE, sheet_name="Museum", dtype=object)
artifact_raw = pd.read_excel(INPUT_FILE, sheet_name="Artifacts", dtype=object)
source_raw = pd.read_excel(INPUT_FILE, sheet_name="Sheet3", dtype=object)

museum_raw.columns = [str(c).strip() for c in museum_raw.columns]
artifact_raw.columns = [str(c).strip() for c in artifact_raw.columns]
source_raw.columns = [str(c).strip() for c in source_raw.columns]

for df in (museum_raw, artifact_raw, source_raw):
    for c in df.columns:
        df[c] = clean_series(df[c])

# ---------- 2. Prepare output folder ----------
if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- 3. Master lookup tables ----------
division = make_lookup(museum_raw["Division"], "Division_ID", "Division_Name")
district_base = museum_raw[["District", "Division"]].copy()
district_base = district_base.dropna(subset=["District"]).copy()
district_base["_dkey"] = district_base["District"].map(key_text)
district_base["_vkey"] = district_base["Division"].map(key_text)
district_base = district_base.drop_duplicates(["_dkey", "_vkey"]).reset_index(drop=True)
district_base["Division_ID"] = district_base["Division"].map(
    lambda x: map_id(x, division, "Division_Name", "Division_ID")
)
district_base = district_base.sort_values(["Division_ID", "District"], key=lambda x: x.astype(str).str.casefold()).reset_index(drop=True)
district_base["District_ID"] = range(1, len(district_base)+1)
district = district_base[["District_ID", "District", "Division_ID"]].rename(columns={"District":"District_Name"})

city_base = museum_raw[["City", "District"]].copy()
city_base = city_base.dropna(subset=["City"]).copy()
city_base["_ckey"] = city_base["City"].map(key_text)
city_base["_dkey"] = city_base["District"].map(key_text)
city_base = city_base.drop_duplicates(["_ckey", "_dkey"]).reset_index(drop=True)

district_map = {
    (key_text(r["District_Name"]), r["Division_ID"]): r["District_ID"]
    for _, r in district.merge(
        district_base[["District_ID", "Division"]], on="District_ID", how="left"
    ).iterrows()
}
# simpler, safe map by city row's district + division through original museum rows
museum_district_div = museum_raw[["District","Division"]].drop_duplicates()
def get_district_id(row):
    dk = key_text(row["District"])
    vk = key_text(row["Division"])
    match = district_base[(district_base["_dkey"]==dk) & (district_base["_vkey"]==vk)]
    return match.iloc[0]["District_ID"] if not match.empty else pd.NA

# city rows can obtain division from original museum records
city_with_div = museum_raw[["City","District","Division"]].dropna(subset=["City"]).copy()
city_with_div["_ckey"] = city_with_div["City"].map(key_text)
city_with_div["_dkey"] = city_with_div["District"].map(key_text)
city_with_div["_vkey"] = city_with_div["Division"].map(key_text)
city_with_div = city_with_div.drop_duplicates(["_ckey","_dkey","_vkey"]).reset_index(drop=True)
city_with_div["District_ID"] = city_with_div.apply(get_district_id, axis=1)
city_with_div = city_with_div.sort_values(["District_ID","City"], key=lambda x: x.astype(str).str.casefold()).reset_index(drop=True)
city_with_div["City_ID"] = range(1, len(city_with_div)+1)
city = city_with_div[["City_ID","City","District_ID"]].rename(columns={"City":"City_Name"})

owner = make_lookup(museum_raw["Owner"], "Owner_ID", "Owner_Name")
category = make_lookup(museum_raw["Category"], "Category_ID", "Category_Name")

# ---------- 4. Museum ----------
museum = museum_raw.copy()
museum["_Museum_Key"] = museum["Museum Name"].map(key_text)
museum = museum.dropna(subset=["Museum Name"]).drop_duplicates("_Museum_Key").reset_index(drop=True)
museum["Museum_ID"] = range(1, len(museum)+1)

def museum_city_id(row):
    ck, dk, vk = key_text(row["City"]), key_text(row["District"]), key_text(row["Division"])
    m = city_with_div[(city_with_div["_ckey"]==ck) & (city_with_div["_dkey"]==dk) & (city_with_div["_vkey"]==vk)]
    return m.iloc[0]["City_ID"] if not m.empty else pd.NA

museum["City_ID"] = museum.apply(museum_city_id, axis=1)
museum["Owner_ID"] = museum["Owner"].map(lambda x: map_id(x, owner, "Owner_Name", "Owner_ID"))
museum["Category_ID"] = museum["Category"].map(lambda x: map_id(x, category, "Category_Name", "Category_ID"))

museum_out = museum[[
    "Museum_ID","City_ID","Museum Name","Owner_ID","Category_ID","Coordinates",
    "Public_Transit_Access","Number_of_Galleries","Established_Date","Opened_as_Museum_Date"
]].rename(columns={"Museum Name":"Museum_Name"})

museum_id_map = dict(zip(museum["Museum Name"].map(key_text), museum["Museum_ID"]))

# ---------- 5. Gallery ----------
gallery_base = artifact_raw[["Museum_Name","Gallery_No"]].copy()
gallery_base = gallery_base.dropna(subset=["Museum_Name","Gallery_No"])
gallery_base["Museum_ID"] = gallery_base["Museum_Name"].map(key_text).map(museum_id_map)
gallery_base = gallery_base.dropna(subset=["Museum_ID"]).copy()
gallery_base["Gallery_No"] = clean_series(gallery_base["Gallery_No"])
gallery_base["_gkey"] = gallery_base["Gallery_No"].map(key_text)
gallery_base = gallery_base.drop_duplicates(["Museum_ID","_gkey"]).sort_values(["Museum_ID","Gallery_No"]).reset_index(drop=True)
gallery = gallery_base[["Museum_ID","Gallery_No"]].copy()
gallery["Gallery_Name"] = gallery["Gallery_No"]
gallery["Floor"] = pd.NA

# ---------- 6. Artifact lookups ----------
artifact_type = make_lookup(artifact_raw["Artifact_Type"], "Artifact_Type_ID", "Artifact_Type_Name")
material = make_lookup(artifact_raw["Material"], "Material_ID", "Material_Name")

# ---------- 7. Dimension ----------
dim_rows = []
dim_map = {}
for v in clean_series(artifact_raw["Dimensions"]).dropna().drop_duplicates():
    k = key_text(v)
    if k in dim_map:
        continue
    length, width, height = parse_dimension(v)
    dim_rows.append({"Dimensions_Raw": v, "Length": length, "Width": width, "Height": height})
    dim_map[k] = len(dim_rows)
dimension = pd.DataFrame(dim_rows)
if dimension.empty:
    dimension = pd.DataFrame(columns=["Dimension_ID","Length","Width","Height"])
else:
    dimension.insert(0, "Dimension_ID", range(1, len(dimension)+1))
    dimension = dimension[["Dimension_ID","Length","Width","Height"]]

# ---------- 8. Artifact ----------
artifact = artifact_raw.copy()
artifact = artifact.dropna(subset=["Museum_Name"]).reset_index(drop=True)
artifact["Artifact_ID"] = range(1, len(artifact)+1)
artifact["Museum_ID"] = artifact["Museum_Name"].map(key_text).map(museum_id_map)
artifact["Artifact_Type_ID"] = artifact["Artifact_Type"].map(lambda x: map_id(x, artifact_type, "Artifact_Type_Name", "Artifact_Type_ID"))
artifact["Material_ID"] = artifact["Material"].map(lambda x: map_id(x, material, "Material_Name", "Material_ID"))
artifact["Dimension_ID"] = artifact["Dimensions"].map(lambda x: dim_map.get(key_text(x), pd.NA))
artifact["Gallery_No"] = artifact["Gallery_No"].map(clean_text)

artifact_out = artifact[[
    "Artifact_ID","Artifact_Name","Museum_ID","Gallery_No","Artifact_Type_ID","Material_ID",
    "Period_Dating","Finding_Place","Dimension_ID","Credit_Donor","Description"
]]

# ---------- 9. Image ----------
image = artifact[["Artifact_ID","Image_URL","Source_Link"]].dropna(subset=["Image_URL"]).copy()
image = image.drop_duplicates(["Artifact_ID","Image_URL"]).reset_index(drop=True)

# ---------- 10. Entry fee ----------
fee_rows = []
fee_columns = {
    "Local": "Entry_Fee_Local_BDT",
    "SAARC": "Entry_Fee_SAARC_BDT",
    "Foreigner": "Entry_Fee_Foreigner_BDT",
    "Others": "Entry_Fee_Others",
}
for _, r in museum.iterrows():
    for fee_type, col in fee_columns.items():
        val = clean_text(r[col])
        if not pd.isna(val):
            fee_rows.append({"Museum_ID": r["Museum_ID"], "Fee_Type": fee_type, "Fee_Amount": val})
entry_fee = pd.DataFrame(fee_rows, columns=["Museum_ID","Fee_Type","Fee_Amount"])

# ---------- 11. Opening hours ----------
opening_hours = museum[["Museum_ID","Opening_Hours"]].dropna(subset=["Opening_Hours"]).copy()
opening_hours = opening_hours.rename(columns={"Opening_Hours":"Opening_Time"})
opening_hours["Day_Name"] = "See Opening_Time"
opening_hours["Closing_Time"] = pd.NA
opening_hours = opening_hours[["Museum_ID","Day_Name","Opening_Time","Closing_Time"]]

# ---------- 12. Closed days ----------
closed_rows = []
for _, r in museum.iterrows():
    for day in split_closed_days(r["Closed_Days"]):
        closed_rows.append({"Museum_ID": r["Museum_ID"], "Closed_Day_Name": day})
closed_days = pd.DataFrame(closed_rows, columns=["Museum_ID","Closed_Day_Name"]).drop_duplicates()

# ---------- 13. Contact ----------
contact = museum[["Museum_ID","Website","Phone","Email"]].copy()
contact = contact.dropna(how="all", subset=["Website","Phone","Email"])

# ---------- 14. Source (Sheet3) ----------
# User rule: only keep rows where Museum_Name matches a museum and URL exists.
source_work = source_raw[["Museum_Name","URL"]].copy()
source_work = source_work.dropna(subset=["Museum_Name","URL"]).copy()
source_work["_Museum_Key"] = source_work["Museum_Name"].map(key_text)
source_work["Museum_ID"] = source_work["_Museum_Key"].map(museum_id_map)
unmatched_sources = source_work[source_work["Museum_ID"].isna()][["Museum_Name","URL"]].copy()
source = source_work.dropna(subset=["Museum_ID"])[["Museum_ID","URL"]].copy()
source = source.drop_duplicates(["Museum_ID","URL"]).rename(columns={"URL":"Source_Link"}).reset_index(drop=True)

# ---------- 15. Save ----------
tables = {
    "division.csv": division,
    "district.csv": district,
    "city.csv": city,
    "owner.csv": owner,
    "category.csv": category,
    "museum.csv": museum_out,
    "gallery.csv": gallery,
    "artifact_type.csv": artifact_type,
    "material.csv": material,
    "dimension.csv": dimension,
    "artifact.csv": artifact_out,
    "image.csv": image,
    "entry_fee.csv": entry_fee,
    "opening_hours.csv": opening_hours,
    "closed_days.csv": closed_days,
    "contact.csv": contact,
    "source.csv": source,
    "unmatched_sheet3_sources.csv": unmatched_sources,
}

for filename, df in tables.items():
    df.to_csv(OUTPUT_DIR / filename, index=False, encoding="utf-8-sig")

print("\n" + "="*65)
print("FINAL DATASET CREATED")
print("="*65)
for filename, df in tables.items():
    print(f"{filename:30s} rows={len(df):5d} cols={len(df.columns):2d}")

print("\nSource table rule:")
print(f"Sheet3 rows with matched museum + URL: {len(source)}")
print(f"Unmatched Sheet3 rows kept only in audit file: {len(unmatched_sources)}")
print(f"\nOutput folder: {OUTPUT_DIR.resolve()}")
