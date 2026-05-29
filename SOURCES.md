# SOURCES.md

## SAP Fuel and Procurement

What I researched: SAP Help Portal documentation for MM60 (Inventory Controlling) and MB51 (Material Document List) transactions. SAP IDoc format documentation via the WE60 transaction. SAP BAPI_GOODSMVT_GETDETAIL documentation.

What I learned: SAP exports are configurable. The same system produces German or English headers depending on the user's language setting. WERKS is plant code, MENGE is quantity, MEINS is base unit of measure, BUDAT is posting date. Dates come in YYYYMMDD format by default. Units are SAP internal codes: L for liters, GAL for gallons, KG for kilograms, MT for metric tonnes. IDoc is binary and EDI-based, used for SAP-to-SAP communication, not practical for third-party ingestion without middleware.

Sample data design: 12 rows across 4 plants (PL01 to PL04, mapped to Mumbai, Delhi, Pune, Chennai). Mixed units (L and GAL) to test conversion logic. One row with a missing unit to trigger flagging. One large bulk procurement row (22,000 liters) to trigger outlier detection. German column headers throughout. Material names include DIESEL-HSD and PETROL-MS so the parser can detect fuel type and apply the correct emission factor (2.68 kgCO2e per liter for diesel, 2.31 for petrol, from DEFRA 2023).

What would break in real deployment: Plant codes are client-specific. My PLANT_LOOKUP dict is fabricated. Real onboarding requires the client's plant master data table before ingestion. Some SAP exports use semicolon delimiters. Date format can vary if regional settings differ. Material numbers need a mapping to fuel type that only the client can provide.

---

## Utility Electricity

What I researched: MSEDCL (Maharashtra State Electricity Distribution Co.) portal export format. Tata Power commercial portal. CEA (Central Electricity Authority) Annual Report 2023 for India grid emission factor.

What I learned: MSEDCL portal exports include consumer number, billing period as a date range, units consumed in kWh, and tariff category. Billing periods almost never align to calendar months. They run meter-read to meter-read, typically 28 to 35 day cycles. The CEA 2023 national grid emission factor for India is 0.716 kgCO2e per kWh. Some large industrial consumers have interval meter data at 15-minute resolution, which we are not handling.

Sample data design: 9 rows with varied billing period formats (date range, month name, YYYY-MM) to stress-test the date parser. One row with a missing meter ID to trigger a flag. One row representing a large industrial consumer at 45,000 kWh to show scale difference from smaller meters.

What would break in real deployment: Different utilities have different CSV column names. There is no standard. A BESCOM (Bangalore) export looks different from MSEDCL. Real deployment needs client-specific column mapping configured before ingestion. Estimated meter reads (marked E vs A in some formats) should be flagged differently from actual reads. We treat them the same.

---

## Corporate Travel

What I researched: Concur Expense API documentation (developer.concur.com), specifically the expense reports and travel trip endpoints. Navan (formerly TripActions) API overview. DEFRA 2023 greenhouse gas conversion factors for business travel (transport and passenger vehicles section).

What I learned: Neither Concur nor Navan provides flight distance in their exports. They provide origin and destination as IATA airport codes. DEFRA's methodology for flight emissions uses great-circle distance with a 1.09 radiative forcing uplift multiplier. Business class emission factors are approximately 2x economy due to seat area. Hotel emissions use a per-night factor (DEFRA 2023: 31 kgCO2e per night). Ground transport is per km. Concur uses cabin class codes like J and C for business class, not just the word "business," so normalization is required.

Sample data design: 6 records covering domestic flight (BOM to DEL), international business class flight (DEL to LHR, 2 travelers), hotel stay in London, international economy flight (BLR to DXB), ground transport in Dubai, and one flight with an unknown airport code (XYZ) to trigger the missing-distance flag.

What would break in real deployment: The airport coordinate lookup covers only 10 major airports. A real deployment needs the full IATA database of roughly 9,000 airports. Concur hotel data includes varying city name formats and sometimes missing night counts. Travel class codes vary across companies (some use J, some use Business, some use Business Class). We handle the common cases but not all edge cases.
