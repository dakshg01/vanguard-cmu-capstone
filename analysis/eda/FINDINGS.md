# EDA findings

- The primary panel has 1,333 snapshots across 49 funds; fiscal calendars and fund starts make it unbalanced.
- The complete 2021–2025 return window retains 263 share classes across 45 primary funds. SPAB CAGR is -0.41%.
- 4 funds trigger the within-fund class-return consistency screen; all original metrics remain saved, but these funds are excluded as a whole from the return-comparison chart pending review. 41 funds remain in that chart. This avoids choosing classes based on better performance.
- Vanguard Core Bond's two class tracking errors over that same window range from 0.344% to 0.375% annualized.
- In March 2026, Vanguard Core Bond's nominal Treasury active weight is -22.40 percentage points, while its reported USD rate sensitivity differs by +0.182 signed years. Allocation and total rate sensitivity answer different questions.
- Flow scale and allocation shift have within-fund Spearman correlation 0.223, with a fund-block bootstrap interval [0.130, 0.303]. This is a contemporaneous descriptive association, not evidence that flows cause trading.
- The swap case reproduces 56 IRS records and separates currency units. The USD-only approximation does not validate an all-currency risk claim.

## Remaining work

Verify reference-class and external security mappings; independently validate sector classifications and filer risk signs; obtain ratings, fees, official benchmark analytics and independent rates/credit factors; expand the historical universe; and verify point-in-time public availability before predictive work. Do not interpret this EDA as a manager-skill ranking.
