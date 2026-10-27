# Qiang sponsor analysis: N-PORT-only first pass

Qiang's October 23 email (PDF pp. 14-17) asks for a fund-quarter positioning table with two layers: normalized sector allocations and active factor exposures. His October 6 instructions (pp. 11-12) specify the common Bloomberg U.S. Aggregate benchmark, a 49-fund primary sample, careful fiscal-date alignment, and warnings about survivorship and cross-family spread-risk conventions. The October 23 instructions supersede the earlier designated-index benchmark suggestion.

His three corrections are: measure swap direction using risk and maturity rather than gross notional; distinguish interest-rate swaps from credit and other swaps; and calculate benchmark weights from actual index-fund filings. This analysis implements those corrections to the extent the supplied data supports them.

## Findings

1. Of 1,333 primary fund snapshots across 49 funds, 1,002 have a same-report-month Aggregate proxy. Complete sector comparisons are available for 882 snapshots across 37 funds. Unmatched or incomplete snapshots remain in the panel with missing active sector values.

2. For Vanguard Core Bond on 2026-03-31, the same-month SPAB proxy gives a nominal Treasury active weight of -22.40 pp, corporate debt (ratings pending) +7.97 pp, and agency MBS +2.32 pp. Half the sum of absolute sector differences is 28.30%. This is sector-level reallocation, not security-level active share.

3. The same case reports USD rate sensitivity of -5.701 signed years versus -5.882 for the proxy: a difference of +0.182 signed years. Large sector reallocations coexist with a much smaller difference in total reported rate sensitivity. Neither derivative market value nor Treasury weight alone measures duration.

4. The sample contains 56 interest-rate swaps among 65 non-FX swap records in the case filing. The other 9 are kept outside the interest-rate bucket. There are 27 pay-fixed and 29 receive-fixed IRS records across currencies. For the 49 eligible USD fixed/floating swaps, the flat-coupon annuity approximation gives a net -0.183 years of duration contribution. This is a rough cross-check, not a replacement for the filed risk or an addition to it.

5. A unit reconciliation remains open with the emailed swap illustration: the filing includes JPY 25.23 billion and HUF 5.44 billion notionals, while eligible USD IRS gross notionals total USD 1.96 billion. Currency-unit notionals cannot be summed and labeled dollars. This USD-only approximation does not reproduce the email's roughly +0.6-year all-swap estimate; seven non-USD IRS records are outside this approximation. Resolve currency conversion and valuation assumptions before treating that estimate as validated.

6. Across primary snapshots, 696 USD rate sensitivities are positive and 617 negative; 12 exceed the 10-year absolute-magnitude diagnostic. Therefore a raw cross-family duration league table would mix conventions. Signed fields and active signed differences are retained for audit, without automatic absolute-value or sign correction.

7. Class-level tracking-error estimates with at least 36 paired months are available for 48 primary funds. These identify index-like behavior for follow-up; they do not identify manager skill. Different class fees, sample windows and proxy tracking differences remain. No reference share class is chosen and no class returns are averaged.

## Methods and limits

- Benchmark: SPAB is the fixed first-choice unadjusted Aggregate proxy; AGG then SCHZ are used only when SPAB lacks the exact report month. Actual proxy ID, report date and lag in days are recorded. There is no nearest-quarter fill, future report substitution, interpolation or calendar-date forward filling. Report-month alignment permits last-business-day versus calendar-month-end differences; exact dates are retained.

- Sector denominator: reported position weights plus separately reported cash outside holdings are normalized to 100%. Original weights, cash and denominator are retained. Delayed-delivery payables remain a separate diagnostic and are not inserted as an extra negative sector. A missing position weight or unreported-cash value makes the snapshot incomplete; incomplete pairs have no active sector output. Negative weights are preserved.

- Classification: SEC asset/issuer codes take precedence. Treasury inflation descriptions identify TIPS; nominal Treasury rows without an inflation description still require CUSIP validation. Agency-name fallback, TBA-description candidates and unresolved positions are auditable. There is no official EM-country membership source here: the fixed study list is exported. Countries outside both study lists remain unresolved (including some sovereigns). Corporate IG/HY ratings are unavailable and remain combined. The Vanguard case has 3.66% in Other / unresolved. Sector completeness refers to input coverage, not independently verified classification accuracy.

- Risk: values use filed DV01 × 10,000 / positive net assets and require all five tenors. They include derivatives already. Sign alignment is not verification of economic duration. Same-sign status and magnitude flags are recorded, but cross-family economic rankings and credit-risk conclusions are withheld. No manual sign convention is assumed.

- Swaps: only explicit DIR/SWP fixed/floating USD legs are included in the approximation. Remaining maturity and the fixed coupon provide a flat annual discount-rate annuity estimate; there is no observed yield curve, schedule, collateral discounting, basis, optionality or FX conversion. Foreign-currency notionals are never added to USD notionals. Missing or ineligible swap records remain in the audit.

- Tracking error: monthly return differences versus the single reported SPAB ETF class; sample standard deviation × sqrt(12), in percent. All rows belonging to an overlapping fund/class/month group are excluded. At least 36 paired observed months are required, with each class's dates shown. These are observed-sample estimates, not common-window performance ranks or alpha estimates.

- Timing and universe: retrospective latest filings, not a point-in-time backtest. The supplied fund list is a current starting snapshot, not a survivorship-free universe. 2026 is partial and latest holdings dates differ by fiscal calendar. No holdings turnover or causal performance claim is made.

## Reproduce

Run `python analyze_sponsor.py` from the project folder. Inputs are read-only; outputs are in `analysis/results`. The HTML report embeds the charts and can be opened directly in a browser.
