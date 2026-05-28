# SOURCES.md

## SAP Fuel & Procurement

**What I researched:** SAP Help Portal documentation for MM60 (Inventory Controlling) and MB51 (Material Document List) transactions. SAP IDoc format documentation (WE60 transaction). SAP BAPI_GOODSMVT_GETDETAIL documentation.

**What I learned:** SAP exports are configurable - the same system can produce German or English headers depending on the user's language setting. `WERKS` (plant), `MENGE` (quantity), `MEINS` (base unit of measure), `BUDAT` (posting date) are the core fields for a goods movement record. Dates come in YYYYMMDD format by default. Units are SAP internal codes — `L` for liters, `GAL` for gallons, `KG` for kilograms, `MT` for metric tonnes.

**Sample data design:** 12 rows covering 4 plants (PL01-PL04 mapped to Mumbai/Delhi/Pune/Chennai). Mix of units (L and GAL) to test conversion. One row with missing unit to test flagging. One large bulk procurement (22,000L) to trigger outlier detection. German column names throughout.

**What would break in real deployment:** Plant codes are client-specific - my `PLANT_LOOKUP` dict is fabricated. Real deployment needs the client's plant master data table. Some SAP exports have semicolon delimiters not commas. Date format can vary if the SAP system's regional settings are non-standard. Material numbers (`MATNR`) need a mapping to fuel type — without it, emission factor selection is guesswork.

---

## Utility Electricity

**What I researched:** MSEDCL (Maharashtra State Electricity Distribution Co.) portal export format. Tata Power commercial portal. CEA (Central Electricity Authority) Annual Report 2023 for India grid emission factor.

**What I learned:** MSEDCL portal exports have consumer number, billing period as a date range, units consumed in kWh, and tariff category. Billing periods almost never align to calendar months -  they run meter-read to meter-read, typically 28-35 day cycles. The CEA 2023 national grid emission factor for India is 0.716 kgCO2e/kWh (CO2 basis). Some large industrial consumers have interval meter data (15-minute readings) - we are not handling that.

**Sample data design:** 9 rows with varied billing period formats (range, month name, YYYY-MM) to stress-test the date parser. One row with missing meter ID. One row representing a large industrial consumer (45,000 kWh) to show scale difference.

**What would break:** Different utilities have different CSV column names - there is no standard. A BESCOM (Bangalore) export looks different from MSEDCL. Real deployment needs client-specific column mapping. Estimated meter reads (marked 'E' vs 'A' in some formats) should be flagged differently from actual reads - we treat them the same.

---

## Corporate Travel

**What I researched:** Concur Expense API documentation (developer.concur.com), specifically the `/expense/reports` and `/travel/trip` endpoints. Navan (formerly TripActions) API overview. DEFRA 2023 greenhouse gas conversion factors for business travel.

**What I learned:** Neither Concur nor Navan provides flight distance — only origin/destination as airport codes (IATA format). DEFRA's methodology for flight emissions uses great-circle distance with a 1.09 radiative forcing uplift multiplier. Business class emission factors are approximately 2x economy due to seat area. Hotel emissions use a per-night factor (DEFRA: 31 kgCO2e/night average UK hotel - used as proxy). Ground transport is per-km.

**Sample data design:** 6 records covering flight (domestic and international), hotel, and ground transport. Business class international flight (BOM→LHR) to test factor difference. One record with unknown airport code (XYZ) to trigger flagging. Multi-traveler record to test per-person multiplication.

**What would break:** Airport coordinate lookup is limited to 10 major airports. A real deployment needs the full IATA database (~9,000 airports). Concur also exports hotel data with varying night counts and city names — our parser assumes `nights` is an integer field, which is not always true. Travel class names vary ("Business", "business", "J", "C") - we only handle the simple cases.
