# Data and methods

Target: full calendar 2024, Europe/Berlin; exclusive end 1 January 2025. Actual coverage is pending retrieval.

| Series | Query | Unit |
|---|---|---|
| DE-LU day-ahead price | A44 | EUR/MWh; XML EUR and MWH |
| Actual demand | A65, A16 | MW; XML MAW |
| Solar, offshore wind, onshore wind | A75, A16; B16, B18, B19 | MW |
| Physical flows, both directions | A11 | MW |

DE-LU EIC: 10Y1001A1001A82H. Borders: AT, BE, CH, CZ, DK1, DK2, FR, NL, NO2, PL, SE4; exact codes and direction parameters are in data.py. Internal DE/LU transfers are excluded. No Germany-only substitute is silently used. Source geography must be checked during first live retrieval.

[ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) is the source. Consult the [API guide](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html) and [token access instructions](https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token). Registration and approved API access are required. Set ENTSOE_API_KEY in the environment. Raw monthly XML and JSON sidecars record query parameters without credentials, units, retrieval UTC and SHA-256. Cached retrieval dates are retained. No retrieval date is claimed before download.

Data rights are separate from code rights. Check current platform terms and the reusable-data list linked from the [ENTSO-E platform information](https://www.entsoe.eu/data/transparency-platform/) before each redistribution; attribution is not blanket permission. Raw data is ignored by Git.

Intervals are left closed, right open. Explicit 15/30/60-minute durations expand to a UTC quarter-hour grid only within each interval. This preserves duration-weighted averages; MW times hours is MWh. Repeated quarter-hour values are not independent observations. Native negative-price intervals and extrema survive resolution changes. Unsupported resolutions and sparse A03 curves fail for review rather than being guessed.

Exact duplicates collapse; conflicting duplicates/overlaps fail. Missing intervals remain missing, never zero-filled or interpolated. Main analysis requires complete coverage for every required series and writes coverage.csv before stopping on gaps. Missing physical flows are not assumed zero. Local daily statistics preserve 23/24/25-hour delivery days. Residual load = actual demand minus wind and solar. Positive net imports = inward minus outward physical flows across listed borders. Daily spread = maximum minus minimum price on a complete local day. Negative means strictly below zero. Episodes cross midnight; missing intervals break runs. Boundary runs are observed lower bounds.

The report selects three distinct days by largest spread, most negative hours and highest mean residual load. Selection is retrospective. Spearman correlations and plots describe associations, not causal effects. Actual fundamentals and physical flows occur after the auction and cannot establish ex-ante forecast skill. Physical flows differ from commercial schedules and include loop flows. Weather, outages, fuel/carbon costs and neighbouring prices are omitted. Spreads are not achievable storage profit. ATR and Bollinger remain optional legacy exploration, not validated hedging rules. Spain/Portugal and controlled sensitivity analysis are future work.
