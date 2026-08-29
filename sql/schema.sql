-- ============================================================
-- MODELBD TOURISM DATABASE -- NORMALIZED (v2)
-- Fixes 1NF violations in Artifact_Type, Material, Credit_Donor,
-- and Contact.Phone from the original submitted schema.
-- ============================================================

DROP DATABASE IF EXISTS modelbd_tourism_v2;

CREATE DATABASE modelbd_tourism_v2
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE modelbd_tourism_v2;


-- ============================================================
-- 1. DIVISION
-- ============================================================

CREATE TABLE Division (
    Division_ID INT PRIMARY KEY,
    Division_Name VARCHAR(100) NOT NULL
);


-- ============================================================
-- 2. OWNER
-- ============================================================

CREATE TABLE Owner (
    Owner_ID INT PRIMARY KEY,
    Owner_Name VARCHAR(255) NOT NULL
);


-- ============================================================
-- 3. CATEGORY
-- ============================================================

CREATE TABLE Category (
    Category_ID INT PRIMARY KEY,
    Category_Name VARCHAR(255) NOT NULL
);


-- ============================================================
-- 4. DISTRICT
-- ============================================================

CREATE TABLE District (
    District_ID INT PRIMARY KEY,
    District_Name VARCHAR(100) NOT NULL,
    Division_ID INT NOT NULL,

    CONSTRAINT fk_district_division
        FOREIGN KEY (Division_ID)
        REFERENCES Division(Division_ID)
);


-- ============================================================
-- 5. CITY
-- ============================================================

CREATE TABLE City (
    City_ID INT PRIMARY KEY,
    City_Name VARCHAR(150) NOT NULL,
    District_ID INT NOT NULL,

    CONSTRAINT fk_city_district
        FOREIGN KEY (District_ID)
        REFERENCES District(District_ID)
);


-- ============================================================
-- 6. MUSEUM
-- ============================================================

CREATE TABLE Museum (
    Museum_ID INT PRIMARY KEY,
    City_ID INT,
    Museum_Name VARCHAR(500) NOT NULL,
    Owner_ID INT,
    Category_ID INT,
    Coordinates VARCHAR(255),
    Public_Transit_Access TEXT,
    Number_of_Galleries INT,
    Established_Date VARCHAR(100),
    Opened_as_Museum_Date VARCHAR(100),

    CONSTRAINT fk_museum_city
        FOREIGN KEY (City_ID)
        REFERENCES City(City_ID),

    CONSTRAINT fk_museum_owner
        FOREIGN KEY (Owner_ID)
        REFERENCES Owner(Owner_ID),

    CONSTRAINT fk_museum_category
        FOREIGN KEY (Category_ID)
        REFERENCES Category(Category_ID)
);


-- ============================================================
-- 7. ARTIFACT_TYPE (now holds ATOMIC tags only, e.g. "Cultural",
--    "Hindu Sculpture", "Shaiva" -- no more "/" or "," composites)
-- ============================================================

CREATE TABLE Artifact_Type (
    Artifact_Type_ID INT PRIMARY KEY,
    Artifact_Type_Name VARCHAR(255) NOT NULL UNIQUE
);


-- ============================================================
-- 8. MATERIAL (now holds ATOMIC tags only)
-- ============================================================

CREATE TABLE Material (
    Material_ID INT PRIMARY KEY,
    Material_Name VARCHAR(255) NOT NULL UNIQUE
);


-- ============================================================
-- 9. DONOR (new -- atomic donor / source entities, split out of
--    the old free-text Credit_Donor column)
-- ============================================================

CREATE TABLE Donor (
    Donor_ID INT PRIMARY KEY,
    Donor_Name VARCHAR(500) NOT NULL UNIQUE
);


-- ============================================================
-- 10. DIMENSION
-- ============================================================

CREATE TABLE Dimension (
    Dimension_ID INT PRIMARY KEY,
    Length VARCHAR(100),
    Width VARCHAR(100),
    Height VARCHAR(100)
);


-- ============================================================
-- 11. GALLERY
-- ============================================================

CREATE TABLE Gallery (
    Museum_ID INT NOT NULL,
    Gallery_No VARCHAR(100) NOT NULL,
    Gallery_Name VARCHAR(255),
    Floor VARCHAR(100),

    PRIMARY KEY (Museum_ID, Gallery_No),

    CONSTRAINT fk_gallery_museum
        FOREIGN KEY (Museum_ID)
        REFERENCES Museum(Museum_ID)
);


-- ============================================================
-- 12. ARTIFACT
--     CHANGED: Artifact_Type_ID, Material_ID, Credit_Donor removed.
--     ADDED: Provenance_Note (original free-text Credit_Donor,
--            preserved verbatim -- see README for why).
--     Type / Material / Donor are now attached via bridge tables
--     below, supporting many-to-many relationships.
-- ============================================================

CREATE TABLE Artifact (
    Artifact_ID INT PRIMARY KEY,
    Artifact_Name VARCHAR(500),
    Museum_ID INT NOT NULL,
    Gallery_No VARCHAR(100),
    Period_Dating VARCHAR(255),
    Finding_Place VARCHAR(500),
    Dimension_ID INT,
    Provenance_Note VARCHAR(500),
    Description TEXT,

    CONSTRAINT fk_artifact_museum
        FOREIGN KEY (Museum_ID)
        REFERENCES Museum(Museum_ID),

    CONSTRAINT fk_artifact_dimension
        FOREIGN KEY (Dimension_ID)
        REFERENCES Dimension(Dimension_ID),

    CONSTRAINT fk_artifact_gallery
        FOREIGN KEY (Museum_ID, Gallery_No)
        REFERENCES Gallery(Museum_ID, Gallery_No)
);


-- ============================================================
-- 13. ARTIFACT_HAS_TYPE (bridge, resolves Artifact <-> Artifact_Type M:N)
-- ============================================================

CREATE TABLE Artifact_Has_Type (
    Artifact_ID INT NOT NULL,
    Artifact_Type_ID INT NOT NULL,

    PRIMARY KEY (Artifact_ID, Artifact_Type_ID),

    CONSTRAINT fk_aht_artifact
        FOREIGN KEY (Artifact_ID)
        REFERENCES Artifact(Artifact_ID),

    CONSTRAINT fk_aht_type
        FOREIGN KEY (Artifact_Type_ID)
        REFERENCES Artifact_Type(Artifact_Type_ID)
);


-- ============================================================
-- 14. ARTIFACT_HAS_MATERIAL (bridge, resolves Artifact <-> Material M:N)
-- ============================================================

CREATE TABLE Artifact_Has_Material (
    Artifact_ID INT NOT NULL,
    Material_ID INT NOT NULL,

    PRIMARY KEY (Artifact_ID, Material_ID),

    CONSTRAINT fk_ahm_artifact
        FOREIGN KEY (Artifact_ID)
        REFERENCES Artifact(Artifact_ID),

    CONSTRAINT fk_ahm_material
        FOREIGN KEY (Material_ID)
        REFERENCES Material(Material_ID)
);


-- ============================================================
-- 15. ARTIFACT_HAS_DONOR (bridge, resolves Artifact <-> Donor M:N)
-- ============================================================

CREATE TABLE Artifact_Has_Donor (
    Artifact_ID INT NOT NULL,
    Donor_ID INT NOT NULL,

    PRIMARY KEY (Artifact_ID, Donor_ID),

    CONSTRAINT fk_ahd_artifact
        FOREIGN KEY (Artifact_ID)
        REFERENCES Artifact(Artifact_ID),

    CONSTRAINT fk_ahd_donor
        FOREIGN KEY (Donor_ID)
        REFERENCES Donor(Donor_ID)
);


-- ============================================================
-- 16. IMAGE
-- ============================================================

CREATE TABLE Image (
    Artifact_ID INT NOT NULL,
    Image_URL TEXT NOT NULL,
    Source_Link TEXT,

    PRIMARY KEY (Artifact_ID, Image_URL(255)),

    CONSTRAINT fk_image_artifact
        FOREIGN KEY (Artifact_ID)
        REFERENCES Artifact(Artifact_ID)
);


-- ============================================================
-- 17. ENTRY_FEE
-- ============================================================

CREATE TABLE Entry_Fee (
    Museum_ID INT NOT NULL,
    Fee_Type VARCHAR(100) NOT NULL,
    Fee_Amount VARCHAR(100),

    PRIMARY KEY (Museum_ID, Fee_Type),

    CONSTRAINT fk_entry_fee_museum
        FOREIGN KEY (Museum_ID)
        REFERENCES Museum(Museum_ID)
);


-- ============================================================
-- 18. OPENING_HOURS
-- ============================================================

CREATE TABLE Opening_Hours (
    Museum_ID INT NOT NULL,
    Day_Name VARCHAR(100) NOT NULL,
    Opening_Time VARCHAR(500),
    Closing_Time VARCHAR(500),

    PRIMARY KEY (Museum_ID, Day_Name),

    CONSTRAINT fk_opening_hours_museum
        FOREIGN KEY (Museum_ID)
        REFERENCES Museum(Museum_ID)
);


-- ============================================================
-- 19. CLOSED_DAYS
-- ============================================================

CREATE TABLE Closed_Days (
    Museum_ID INT NOT NULL,
    Closed_Day_Name VARCHAR(100) NOT NULL,

    PRIMARY KEY (Museum_ID),

    CONSTRAINT fk_closed_days_museum
        FOREIGN KEY (Museum_ID)
        REFERENCES Museum(Museum_ID)
);


-- ============================================================
-- 20. CONTACT
--     CHANGED: Phone column removed (was multi-valued,
--     e.g. "880247391933; 01832717017; 01926081326").
--     Replaced by Museum_Phone below.
-- ============================================================

CREATE TABLE Contact (
    Museum_ID INT PRIMARY KEY,
    Website TEXT,
    Email VARCHAR(255),

    CONSTRAINT fk_contact_museum
        FOREIGN KEY (Museum_ID)
        REFERENCES Museum(Museum_ID)
);


-- ============================================================
-- 21. MUSEUM_PHONE (new -- one row per phone number per museum)
-- ============================================================

CREATE TABLE Museum_Phone (
    Museum_ID INT NOT NULL,
    Phone_Number VARCHAR(50) NOT NULL,

    PRIMARY KEY (Museum_ID, Phone_Number),

    CONSTRAINT fk_museum_phone_museum
        FOREIGN KEY (Museum_ID)
        REFERENCES Museum(Museum_ID)
);


-- ============================================================
-- 22. SOURCE
-- ============================================================

CREATE TABLE Source (
    Museum_ID INT NOT NULL,
    Source_Link TEXT NOT NULL,

    PRIMARY KEY (Museum_ID, Source_Link(255)),

    CONSTRAINT fk_source_museum
        FOREIGN KEY (Museum_ID)
        REFERENCES Museum(Museum_ID)
);
