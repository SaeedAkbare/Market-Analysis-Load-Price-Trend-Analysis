# Data and methods — public-source reconstruction

The default source is the [Fraunhofer ISE Energy-Charts v2 API](https://api.energy-charts.info/). No token or account is required. This documented API supplies prices attributed to Bundesnetzagentur | SMARD.de, and physical series published by Energy-Charts. It is an alternative distribution route, not a claim that every value was fetched directly from ENTSO-E.

Target: 1 January–31 December 2024, Europe/Berlin; exclusive end 1 January 2025. Three full-year requests are cached with URLs, actual retrieval UTC, license, source metadata and SHA-256. Requests use inclusive calendar-date parameters; alignment uses an exclusive end. Rate-limit responses honour numeric Retry-After up to 60 seconds, then stop for a later retry. The optional original ENTSO-E adapter remains in data.py; its documentation is preserved in entsoe-methods-legacy.md.

| Endpoint | Selection | Source unit | Analysis unit / scope |
|---|---|---|---|
| /v2/price | bzn=DE-LU, day_ahead_price | EUR / MWh | EUR/MWh, DE-LU bidding zone |
| /v2/public_power | country=de; load, wind_onshore, wind_offshore, solar | MW | MW, Germany |
| /v2/cbpf | country=de, named borders | GW | MW, Germany physical border flows |

Physical border series are Austria, Belgium, Czech Republic, Denmark, France, Luxembourg, Netherlands, Norway, Poland, Sweden and Switzerland. Denmark and Norway are country aggregates here, not separate bidding zones. Luxembourg is included because these flows describe Germany, not the DE-LU boundary. These fundamentals must not be labelled a complete DE-LU balance. Load is the provider's load series; generation is public net generation, not a measure of all industrial self-supply. Residual load is calculated as this load minus wind and solar from the same source.

Positive source flows mean imports. GW is multiplied by 1,000 to obtain MW. Positive/negative parts produce inward/outward *net border flow*, not gross simultaneous directional measurements. Provider sum is excluded from summation and used only for a consistency check, with 12 MW tolerance for rounded border values. The total includes the Luxembourg border.

All timestamps mark interval starts. Offset-aware timestamps convert to UTC; daily summaries use Europe/Berlin. Returned interval_minutes is required (15, 30 or 60); each value is repeated only within its explicit interval on a quarter-hour grid. This is duration weighting, not interpolation. Nulls remain missing. Exact duplicates collapse, conflicts fail. Unsupported or mixed-resolution metadata stops retrieval for split-period handling rather than inferring a duration from gaps. For this fixed 2024 analysis, the live responses supply hourly prices and quarter-hour physical series. A future period crossing a resolution change needs requests split at that transition.

Coverage is checked for every required series, and findings require full coverage. Daily spreads use complete local days (23/24/25 hours). Negative prices are strictly below zero, durations are measured in hours, and runs cross midnight. Sample-boundary runs are censored. Repeated price values are not independent samples. Correlations are descriptive Spearman associations, without causal or significance claims.

Responses retrieved for this run identify CC BY 4.0: credit Energy-Charts.info for physical data and Bundesnetzagentur | SMARD.de for prices. Check each response's license before applying the adapter to other zones. Raw data stays outside Git; derived figures/tables and provenance summaries may be shared with attribution and notice of transformation. See [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Three distinct retrospective case days are selected by maximum spread, negative hours and mean residual load. No causal event explanation is inferred from these rankings. Weather, outages, fuels, carbon and neighbouring prices remain omitted. Actual fundamentals are ex post; spreads are not storage profits. Spain/Portugal and controls for seasonality remain future extensions.
