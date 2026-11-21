# Vanguard / CMU capstone: revision package v4 (21 Nov 2026)

Responds to the sponsor feedback of 18 Nov 2026 (Qiang Song, Vanguard) and the team's WhatsApp notes (iron out Layer 2 and add more coefficients for other funds; active duration looked wrong; returns in percent vs decimal).
The presentation deck has NOT been rebuilt for v4. The last delivered deck (Vanguard_Capstone_Presentation_v3.pptx, 42 slides) reflects v3 numbers, before the sector overrides and the model-selection rule below.

## 1. Short summary

Corrected in the data
* Units error: three funds had some months filed as decimals instead of percent. These are Allspring Core Plus (36 months), Diamond Hill Core (9) and Voya Intermediate (15), and I rescaled them.
* Allspring's rank: its raw 2021-2025 rank drops from 1 to 19 of 46. Eaton Vance, Dodge & Cox and Victory are now the top three.
* Putnam: its history now starts in March 2023, when it became a core fund.
* Duration screen: 40 implausible duration readings are blanked, including Vanguard Core's December 2019 value.

New on the slides (v3 deck)
* Where Vanguard sits: tracking error, information ratio, fees and turnover for the three Vanguard funds.
* Vanguard Core measured against both SPAB and the float-adjusted Aggregate.
* A rebuilt duration slide.
* The Layer 2 factor table, plus a scatter of every fund's rate and credit loadings.
* Appendix slides on the units check and the duration screen.
* Candidates are labelled Fund A/B/C.

To raise with Qiang
* Peer median: I couldn't reproduce his point that Vanguard Core's raw return moves closer to the peer median after the units fix. The peer median stays at 2.7%.
* 2022 agency MBS: his statement that agency MBS underperformed in 2022 conflicts with the data (MBB -11.7% vs SPAB -13.2%). I left it off the slides.

## 2. How the package is organised

| Path | Contents |
|---|---|
| Vanguard_Full_Analysis_With_Bloomberg_v4.ipynb | Full pipeline. Runs end to end (about 90 seconds). Supersedes v2 (team original) and v3 |
| inputs_optional/sector_overrides.csv | Reviewed sector reclassifications read by the notebook (revision D) |
| tables/ | Result tables (CSV/JSON) |
| audit/ | Data-quality audit tables |
| sponsor/ | Tables and JSON behind the presentation slides (includes presentation_data.json, summary.json) |
| charts/ | Static charts (PNG/SVG), including new chart 17_layer2_rate_vs_credit_loadings |
| CHANGELOG_v4.md | Short change log for v4. CHANGELOG_v3.md (sent earlier) covers v3 |

Notebook versions: v2 is the team's original. v3 adds revisions A-C and E-F. v4 adds D (overrides, input file) and G (model-selection rule).
Competitor names appear in the tables (internal Vanguard audience). Anonymize before sharing outside Vanguard.
Qiang's internal Vanguard Core duration series (xlsx) is for checking only and is not used in any file in this package.

## 3. Revisions made, file by file

### A. Return-units check and correction (notebook cell 7; v3)
* Problem: some funds' N-PORT monthly returns were filed as decimals (0.0123) rather than percent (1.23), which distorted rankings.
* Method: for each class and filing, the sum of absolute monthly returns is compared with the SPAB proxy over the same months. A ratio of 0.3%-8% marks a decimal-scaled filing. It is multiplied by 100 and must then look like an ordinary return series. Filings with too little market movement to test inherit the flag only if their testable neighbours are flagged. Near-zero filings are reported, not rescaled. The band is set in CFG as units_ratio_range.
* Corrected: Allspring Core Plus (36 months, 2019-09 to 2022-08), Diamond Hill Core (9, 2019-07 to 2020-03), Voya Intermediate (15, 2019-07 to 2020-09).
* New audit files: audit/units_check_filings.csv, units_corrected_return_rows.csv, units_correction_summary.csv, near_zero_return_filings.csv.
* Updated files that consume returns (anything touching returns changed): tables/fund_month_returns.csv, performance_metrics.csv, annual_performance.csv, annual_peer_summary.csv, annual_rank_persistence.csv, fund_scorecards.csv, factor_model_estimates.csv, factor_loadings.csv, joint_zero_alpha_bootstrap.csv, bootstrap_block_sensitivity.csv, stress_performance.csv, vanguard_scorecards.csv, ml_* tables; sponsor/ comparable_windows, covid_matched_alpha, stress_all_available, fee_association, vanguard_relative_wealth and others.
* Result changes: Allspring Core Plus's raw 2021-2025 rank 1 -> 19 of 46. New top three on relative growth: Eaton Vance, Dodge & Cox, Victory. Benchmark-beating counts, annual peer summaries, persistence and bootstrap results were recomputed on corrected returns.
* Not changed: Diamond Hill's early months remain quarantined (no published 2020 reconciliation). Federated Hermes filings with near-zero returns in 2023-2024 are reported (audit/near_zero_return_filings.csv) but not rescaled, because they do not fit a decimal-scaling pattern.

### B. Putnam Core Bond start date (CFG fund_start_overrides; v3)
* Putnam Core Bond was the Fixed Income Absolute Return Fund until 28 Feb 2023. Returns and positions before 2023-03-01 are excluded.
* Effect: Putnam is excluded from the complete 2021-2025 sample (funds with complete history 47 -> 46) and from the rankings; it still appears with its shorter history.
* Files: audit/quarantined_class_returns.csv, tables/fund_scorecards.csv, ranking and ML tables.

### C. Duration plausibility screen (notebook cell 11; v3)
* Problem: Vanguard Core's active duration showed a +2.2 year spike around December 2019.
* Method: a reported duration more than 1.0 year from the fund's own centred 5-quarter median is treated as a likely filing error and blanked in the duration scenario (source values kept). Setting: CFG duration_outlier_years.
* Result: 40 snapshots flagged across all funds (audit/duration_outlier_flags.csv), including the Vanguard Core December 2019 reading. Signs of reported duration remain unverified (sign-normalised scenario only).
* Files: audit/duration_outlier_flags.csv; sponsor/position_bands.csv, duration_yields.csv, duration_lead_association.csv; tables/holdings_rate_attribution_scenario.csv; chart 08_active_duration_scenario.

### D. Reviewed sector overrides for unclassified holdings (v4, new input file)
* Why: BlackRock showed 66% and Federated 42% average unresolved weight.
* Findings. BlackRock Total Return filed one "Master Total Return Portfolio" line (100% of the fund) through June 2024, so the real holdings sit in the master fund's own filing. From Sept 2024 holdings are visible and classified (1.4%-4.9% unresolved). Federated Hermes Total Return holds other Federated Core Trust funds: Mortgage Core (about 24%), Project & Trade Finance (about 5%), High Yield (about 5%), Bank Loan (about 4%), plus money market funds.
* Changes made (inputs_optional/sector_overrides.csv, 218 fund-quarters across 18 funds), only where the holding's economic identity is clear: money-market funds -> Cash; high-yield, bank-loan and floating-rate funds and corporate-bond ETFs -> Corporate; CLO ETFs -> ABS/CLO; EM local-currency funds -> Emerging markets. Source: audit sample classification_review_sample.csv. The notebook applies them to normalised weights only; raw weights are unchanged.
* Results: fund-quarters passing the 10% unresolved screen 1,133 -> 1,140 (TCW MetWest +4, Goldman Sachs +3). Average unresolved weight: Federated 42.2% -> 34.7% (still excluded), TCW MetWest 12.2% -> 1.9%, Goldman 5.6% -> 1.4%, Bridge Builder Core and Core-Plus about 3.9%/3.4% -> about 0%.
* Files updated: audit/classification_quality.csv, tables/active_positions.csv, positioning_summary.csv, quarterly_position_chart_panel.csv, quarterly_positioning_sample_counts.csv, fund_scorecards.csv, layer2_factor_table.csv, benchmark_match_sensitivity.csv, ml_* tables, sponsor/ outputs.
* Deliberately NOT reclassified (no data on their contents): Federated Mortgage Core Portfolio, Federated Project & Trade Finance Core, the unnamed Federated "Core Trust mutual fund", Fidelity Mortgage Backed Securities Central Fund, DoubleLine funds, ultra-short ETFs, and sovereign or supranational bonds outside the country lists (Dominican Republic, Uruguay, Greece, development banks).

### E. Agency MBS coded as corporate check (v4; analysis only, no file changes)
* Vanguard Core (March 2026, the only fund with security-level holdings in the project): no material misclassification. Mortgage-named bonds outside the MBS category are mortgage-company bonds (Rocket, Freedom) and are correctly corporate.
* Inconsistency found: Freddie Mac STACR and Fannie Mae CAS credit-risk-transfer notes are treated inconsistently (some agency via name fallback, some non-agency). About 0.1%-0.2% of Vanguard Core. Not changed.
* Competitor funds were NOT checked (see section 4).

### F. Vanguard benchmark, Layer 2 and additional analysis (notebook section 17; v3)
* Float-adjusted benchmark: the Vanguard Total Bond Market Index fund (S000002564), computed from its own N-PORT filings matched to each report date, as an alternative to SPAB for Vanguard funds (tables/vanguard_float_benchmark_comparison.csv, vanguard_float_adjusted_positions.csv).
* Vanguard Core results. Against SPAB: relative wealth 4.77%, tracking error 0.49%, information ratio 1.38, tracking error rank 1 of 11 and information ratio rank 1 of 11 among the fund and its 10 matched peers. Against float-adjusted: 5.15%, 0.52%, 1.40. Active duration against the float-adjusted proxy stays within about half a year since 2020.
* Layer 2 factor table (tables/layer2_factor_table.csv, 1,333 fund-quarters, 1,140 passing the position screen): one row per fund per quarter with active duration, curve, non-USD rates, agency MBS, TIPS, spread duration, credit quality placeholder and a rolling 36-month rate/credit loading. Loadings for all funds: layer2_loadings_all_funds.csv, layer2_f8_rolling_36m.csv; chart 17_layer2_rate_vs_credit_loadings. This answers the "add more coefficients for other funds" note. Vanguard Core's full-sample factor-model loadings are rate +0.18 and credit +0.54 against Core-peer medians of -0.34 and +0.59.
* Comparable windows (same months for Vanguard and peers): Core 83 months, 4.73% against a peer median of 2.70% (10 peers); Core-Plus 56 months, 4.59% against 1.27% (26 peers); STAR 15 months, 1.65% against 0.28% (26 peers).
* Excluding 2020: median factor alpha across 45 matched funds 46.4 bp -> 23.2 bp; Vanguard Core 71.9 bp -> 30.5 bp.
* Fee proxy / turnover: Vanguard Core 10 bp / 439%; Core-Plus 20 bp / 488%; STAR 20 bp. Core peer median 32.5 bp / 122%; Core-Plus peers 38 bp / about 132%.

### G. Model-selection rule (notebook, sponsor section; v4)
* Problem: after revision D added three fund-quarters, the lowest-RMSE rule flipped the selected model from OLS to boosting on a margin of 0.08 bp of quarterly RMSE (84.14 vs 84.22). That margin is noise.
* Change: the rule is now fixed in advance. OLS is the baseline. A nonlinear model replaces it only if its paired-bootstrap RMSE gain over OLS (500 resamples of calendar quarters) has a 95% interval that excludes zero. Methodology text in the notebook updated to match. New table: sponsor/model_selection_rule.csv.
* Result: OLS selected. Gains over OLS: elastic net -2.4% (interval -4.6 to +1.1), random forest -3.0% (-9.0 to +9.2), boosting -1.2% (-6.0 to +7.7). All include zero, so nonlinear models give no meaningful improvement.
* Effect on numbers (v3 -> v4, whole-fund holdout fund-equal RMSE, bp): OLS 83.4 -> 84.2; elastic net 84.3 -> 85.8; random forest 85.4 -> 85.5; boosting 84.5 -> 84.1. Competitor training rows 1,010 -> 1,013.
* Vanguard residual (mean quarterly, OLS, bp): Core 14.6 (unchanged), Core-Plus 4.9 -> 6.3, STAR -2.9 -> -2.1. Caveat: the residual depends on the model. Under boosting, Vanguard Core's residual is only 0.5 bp, so a positive residual is not evidence of skill.

### H. Benchmark-age sensitivity (checked, no change)
* Usable fund-quarters: 803 with same-day benchmark reports, 1,135 within 45 days, 1,140 within 100 days (the setting used). Results barely move between 45 and 100 days. Table: tables/benchmark_match_sensitivity.csv.

## 4. Revisions not done, and why

| Item | Why not possible now | What would unblock it |
|---|---|---|
| Credit quality (factor 7) | Needs issuer ratings from Bloomberg; none in the project. Corporate weights are unrated | A Bloomberg ratings export |
| Qiang's "closer to peer median" claim | Not reproducible: after the units fix the Core peer median stays at 2.7% | Qiang's exact comparison or inputs |
| Qiang's "agency MBS underperformed in 2022" | Conflicts with data (MBB -11.7%, SPAB -13.2% in 2022) | Qiang's source |
| Duration signs | Reported duration signs cannot be verified from filings; the duration chart is a sign-normalised scenario. Qiang's series is for checking only and is not used in shared material | Published duration data from an external source |
| Agency MBS coded as corporate, competitor funds | Raw N-PORT holdings for competitors are not in the project (data/zips is empty); only Vanguard Core holdings exist | Raw N-PORT holdings files |
| BlackRock master-fund look-through (through June 2024) | The master fund's own filing is not in the data | The master fund's N-PORT filings |
| Federated and Fidelity mortgage-fund look-through | Their mortgage mix is unknown | The underlying funds' holdings |
| Federated Hermes near-zero returns | Not a decimal-scaling pattern; cause unknown (stale data or fund feature) | Source filings or the fund's published returns |
| Sovereign and supranational unclassified holdings | Judgment calls (for example, Greece developed vs emerging). Not applied | Team decision on country classification |
| Deck rebuild with v4 numbers | Deferred on request until numbers are final | Approval of v4 results |

Other limitations carried forward:
* ML results differ slightly from the team's original run because of library versions (pandas 2.2.3 required). The conclusion is the same.
* Layer 2 factors 3, 5 and 6 (non-USD rates, TIPS, spread duration) are partial or not comparable across fund families.
* The deck must be updated for v4: model slides (selected model, RMSEs, training rows), the residual slide caveat, and the band charts and Layer 2 peer ranges, which move slightly with the 7 added fund-quarters.
