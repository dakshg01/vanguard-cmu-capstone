# Complete database field catalogue

Generated from the current SQLite schema and the SEC metadata retained with the archives.

There are 71 physical tables and 51 saved views. A view has no independent stored rows; it is a saved query. Most apparent duplication comes from raw text tables, typed tables, and latest-filing views over the same source families.

SEC source descriptions use the latest supplied archive that contains each table/column. Types in computed views can be blank because SQLite does not declare a type for every expression. Raw tables retain text even when the source metadata defines a numeric/date field. Blank descriptions indicate no additional description was supplied here; consult the corresponding SEC source table and README.

## `archives` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `archive_id` | TEXT |  |
| `filename` | TEXT |  |
| `bytes` | INTEGER |  |
| `loaded_at` | TEXT |  |

## `derivative_pnl_all` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `month_end` | TEXT | Calendar month-end associated with the monthly observation. |
| `asset_category` | TEXT |  |
| `instrument_kind` | TEXT |  |
| `month_slot` | INTEGER | Source month slot: 1 oldest, 3 newest, anchored to report month. |
| `realized_pnl_usd` | REAL |  |
| `unrealized_change_usd` | REAL |  |

## `filings_all` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `cik` | TEXT |  |
| `series_name` | TEXT |  |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `report_month` | TEXT | Report date aligned to calendar month-end; the exact report_date is retained. |
| `fiscal_year_end` | TEXT |  |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `submission_type` | TEXT |  |
| `is_last_filing` | TEXT |  |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |
| `total_assets` | REAL |  |
| `total_liabilities` | REAL |  |
| `net_assets` | REAL |  |

## `ingest_issues` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `archive_id` | TEXT |  |
| `table_name` | TEXT |  |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `column_name` | TEXT |  |
| `raw_value` | TEXT |  |
| `reason` | TEXT |  |

## `inventory` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `archive_id` | TEXT |  |
| `table_name` | TEXT |  |
| `source_rows` | INTEGER |  |
| `retained_rows` | INTEGER |  |
| `columns_json` | TEXT |  |

## `monthly_flows_all` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `month_end` | TEXT | Calendar month-end associated with the monthly observation. |
| `month_slot` | INTEGER | Source month slot: 1 oldest, 3 newest, anchored to report month. |
| `sales_usd` | REAL |  |
| `reinvestment_usd` | REAL |  |
| `redemptions_usd` | REAL |  |
| `net_external_flow_usd` | REAL | sales_usd minus redemptions_usd; excludes reinvestment. |
| `net_flow_including_reinvestment_usd` | REAL | sales_usd + reinvestment_usd - redemptions_usd. |
| `nonderivative_realized_pnl_usd` | REAL |  |
| `nonderivative_unrealized_change_usd` | REAL |  |

## `monthly_returns_all` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `month_end` | TEXT | Calendar month-end associated with the monthly observation. |
| `return_row_id` | TEXT |  |
| `class_id` | TEXT |  |
| `month_slot` | INTEGER | Source month slot: 1 oldest, 3 newest, anchored to report month. |
| `return_pct` | REAL | Monthly share-class return in percentage points: 1.25 means 1.25%. |
| `return_decimal` | REAL | Monthly share-class return as a decimal: 0.0125 means 1.25%. |

## `raw_borrow_aggregate` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `BORROW_AGGREGATE_ID` | TEXT | Surrogate Key |
| `AMOUNT` | TEXT | Aggregate principal amount |
| `COLLATERAL` | TEXT | Aggregate value of collateral |
| `INVESTMENT_CAT` | TEXT | Category of investments |
| `OTHER_DESC` | TEXT | Brief description if category of investment is Other Instrument |

## `raw_borrower` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `BORROWER_ID` | TEXT | Surrogate Key |
| `NAME` | TEXT | Name of borrower |
| `LEI` | TEXT | LEI (if any) of borrower. |
| `AGGREGATE_VALUE` | TEXT | Aggregate value of all securities on loan to the borrower. |

## `raw_convertible_security_currency` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `CONVERTIBLE_SECURITY_ID` | TEXT | Surrogate Key |
| `CONVERSION_RATIO` | TEXT | Conversion ratio |
| `CURRENCY_CODE` | TEXT | Currency code |

## `raw_debt_security` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `MATURITY_DATE` | TEXT | Maturity date |
| `COUPON_TYPE` | TEXT | The category that most closely reflects the coupon type among the following: fixed, floating, variable, none. |
| `ANNUALIZED_RATE` | TEXT | Annualized rate. |
| `IS_DEFAULT` | TEXT | Currently in default |
| `ARE_ANY_INTEREST_PAYMENT` | TEXT | Are there any interest payments in arrears or have any coupon payments been legally deferred by the issuer |
| `IS_ANY_PORTION_INTEREST_PAID` | TEXT | Is any portion of the interest paid in kind? |
| `IS_CONVTIBLE_MANDATORY` | TEXT | Is it Mandatory convertible |
| `IS_CONVTIBLE_CONTINGENT` | TEXT | Is it Contingent convertible |

## `raw_debt_security_ref_instrument` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DEBT_SECURITY_REF_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Name of issuer |
| `ISSUE_TITLE` | TEXT | Title of issue |
| `CURRENCY_CODE` | TEXT | Currency code |
| `CUSIP` | TEXT | CUSIP of reference instrument |
| `ISIN` | TEXT | ISIN |
| `TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_DESC` | TEXT | Type of identifier if 'other' identifier provided |

## `raw_derivative_counterparty` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DERIVATIVE_COUNTERPARTY_ID` | TEXT | Surrogate Key |
| `DERIVATIVE_COUNTERPARTY_NAME` | TEXT | Name of counterparty |
| `DERIVATIVE_COUNTERPARTY_LEI` | TEXT | LEI (if any) of counterparty |

## `raw_desc_ref_index_basket` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `INDEX_NAME` | TEXT | Index Name |
| `INDEX_IDENTIFIER` | TEXT | Index Identifier |
| `NARRATIVE_DESC` | TEXT | Narrative Description |

## `raw_desc_ref_index_component` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DESC_REF_INDEX_COMPONENT_ID` | TEXT | Surrogate Key |
| `NAME` | TEXT | Name of component |
| `CUSIP` | TEXT | CUSIP |
| `ISIN` | TEXT | ISIN |
| `TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_DESC` | TEXT | Other identifier type used |
| `NOTIONAL_AMOUNT` | TEXT | Notional amount |
| `CURRENCY_CODE` | TEXT | Currency code |
| `VALUE` | TEXT | Value |
| `ISSUER_CURRENCY_CODE` | TEXT | Currency code of issuer |

## `raw_desc_ref_other` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DESC_REF_OTHER_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Issuer name |
| `ISSUE_TITLE` | TEXT | Issuer title |
| `CUSIP` | TEXT | CUSIP |
| `ISIN` | TEXT | ISIN |
| `TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_DESC` | TEXT | Other identifier type used |

## `raw_explanatory_note` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `EXPLANATORY_NOTE_ID` | TEXT | Surrogate Key |
| `ITEM_NO` | TEXT | Item number |
| `EXPLANATORY_NOTE` | TEXT | Explanatory note |

## `raw_floating_rate_reset_tenor` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `RATE_RESET_TENOR_ID` | TEXT | Surrogate Key |
| `RECEIPT_OR_PAYMENT` | TEXT | Receipt or payment |
| `RESET_DATE` | TEXT | Rate reset date |
| `RESET_DATE_UNIT` | TEXT | Rate reset unit |
| `RATE_TENOR` | TEXT | Rate tenor |
| `RATE_TENOR_UNIT` | TEXT | Rate tenor unit |

## `raw_fund_reported_holding` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `HOLDING_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Name of issuer |
| `ISSUER_LEI` | TEXT | LEI (if any) of issuer. In the case of a holding in a fund that is a series of a series trust, report the LEI of the series |
| `ISSUER_TITLE` | TEXT | Title of the issue or description of the investment. |
| `ISSUER_CUSIP` | TEXT | CUSIP |
| `BALANCE` | TEXT | Balance |
| `UNIT` | TEXT | Indicate whether balance amount is expressed in number of shares, principal amount, or other units |
| `OTHER_UNIT_DESC` | TEXT | Other units description |
| `CURRENCY_CODE` | TEXT | Currency code |
| `CURRENCY_VALUE` | TEXT | Value |
| `EXCHANGE_RATE` | TEXT | Exchange rate |
| `PERCENTAGE` | TEXT | Percentage value compared to net assets of the Fund |
| `PAYOFF_PROFILE` | TEXT | Payoff profile -- long, short, N/A |
| `ASSET_CAT` | TEXT | Asset type |
| `OTHER_ASSET` | TEXT | If Asset type is Other, provide a brief description. |
| `ISSUER_TYPE` | TEXT | Issuer type |
| `OTHER_ISSUER` | TEXT | If Issuer type is Other, provide a brief description. |
| `INVESTMENT_COUNTRY` | TEXT | Report the ISO country code that corresponds to the country where the issuer is organized |
| `IS_RESTRICTED_SECURITY` | TEXT | Is the investment a Restricted Security |
| `FAIR_VALUE_LEVEL` | TEXT | The level within the fair value hierarchy in which the fair value measurements fall pursuant  to US GAAP |
| `DERIVATIVE_CAT` | TEXT | Type of derivative instrument |

## `raw_fund_reported_info` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `SERIES_NAME` | TEXT | Name of Series |
| `SERIES_ID` | TEXT | EDGAR Series Identifier |
| `SERIES_LEI` | TEXT | LEI of Series. |
| `TOTAL_ASSETS` | TEXT | Total assets |
| `TOTAL_LIABILITIES` | TEXT | Total liabilities |
| `NET_ASSETS` | TEXT | Net assets |
| `ASSETS_ATTRBT_TO_MISC_SECURITY` | TEXT | Assets attributable to miscellaneous securities |
| `ASSETS_INVESTED` | TEXT | Assets invested in a Controlled Foreign Corporation |
| `BORROWING_PAY_WITHIN_1YR` | TEXT | Amounts payable to banks or other financial institutions for borrowings within one year |
| `CTRLD_COMPANIES_PAY_WITHIN_1YR` | TEXT | Amounts payable to controlled companies within one year |
| `OTHER_AFFILIA_PAY_WITHIN_1YR` | TEXT | Amounts payable to other affiliates within one year |
| `OTHER_PAY_WITHIN_1YR` | TEXT | Amounts payable to others within one year |
| `BORROWING_PAY_AFTER_1YR` | TEXT | Amounts payable to banks or other financial institutions for borrowings after one year |
| `CTRLD_COMPANIES_PAY_AFTER_1YR` | TEXT | Amounts payable to controlled companies after one year |
| `OTHER_AFFILIA_PAY_AFTER_1YR` | TEXT | Amounts payable to other affiliates after one year |
| `OTHER_PAY_AFTER_1YR` | TEXT | Amounts payable to others after one year |
| `DELAYED_DELIVERY` | TEXT | Payables for investments purchased on a delayed delivery, when-issued, or other firm commitment basis |
| `STANDBY_COMMITMENT` | TEXT | Payables for investments purchased on a standby commitment basis |
| `LIQUIDATION_PREFERENCE` | TEXT | Liquidation preference of outstanding preferred stock issued by the Fund |
| `CASH_NOT_RPTD_IN_C_OR_D` | TEXT | Cash and cash equivalents not reported in Parts C or D |
| `CREDIT_SPREAD_3MON_INVEST` | TEXT | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 3 month maturity |
| `CREDIT_SPREAD_1YR_INVEST` | TEXT | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 1 year maturity |
| `CREDIT_SPREAD_5YR_INVEST` | TEXT | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 5 year maturity |
| `CREDIT_SPREAD_10YR_INVEST` | TEXT | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 10 year maturity |
| `CREDIT_SPREAD_30YR_INVEST` | TEXT | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 30 year maturity |
| `CREDIT_SPREAD_3MON_NONINVEST` | TEXT | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 3 month maturity |
| `CREDIT_SPREAD_1YR_NONINVEST` | TEXT | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 1 year maturity |
| `CREDIT_SPREAD_5YR_NONINVEST` | TEXT | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 5 year maturity |
| `CREDIT_SPREAD_10YR_NONINVEST` | TEXT | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 10 year maturity |
| `CREDIT_SPREAD_30YR_NONINVEST` | TEXT | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 30 year maturity |
| `IS_NON_CASH_COLLATERAL` | TEXT | Did any securities lending counterparty provide any non-cash collateral |
| `NET_REALIZE_GAIN_NONDERIV_MON1` | TEXT | First month net realized gain (loss) attributable to investments other than derivatives |
| `NET_UNREALIZE_AP_NONDERIV_MON1` | TEXT | First month net change in unrealized appreciation (or depreciation) attributable to investments other than derivatives |
| `NET_REALIZE_GAIN_NONDERIV_MON2` | TEXT | Second month net realized gain (loss) attributable to investments other than derivatives |
| `NET_UNREALIZE_AP_NONDERIV_MON2` | TEXT | Second month net change in unrealized appreciation (or depreciation) attributable to investments other than derivatives |
| `NET_REALIZE_GAIN_NONDERIV_MON3` | TEXT | Third month net realized gain (loss) attributable to investments other than derivatives |
| `NET_UNREALIZE_AP_NONDERIV_MON3` | TEXT | Third month net change in unrealized appreciation (or depreciation) attributable to investments other than derivatives |
| `SALES_FLOW_MON1` | TEXT | First Month Total net asset value of shares sold |
| `REINVESTMENT_FLOW_MON1` | TEXT | First Month Total net asset value of shares sold in connection with reinvestments of dividends and distributions |
| `REDEMPTION_FLOW_MON1` | TEXT | First Month Total net asset value of shares redeemed or repurchased, including exchanges |
| `SALES_FLOW_MON2` | TEXT | Second Month Total net asset value of shares sold |
| `REINVESTMENT_FLOW_MON2` | TEXT | Second Month Total net asset value of shares sold in connection with reinvestments of dividends and distributions |
| `REDEMPTION_FLOW_MON2` | TEXT | Second Month Total net asset value of shares redeemed or repurchased, including exchanges |
| `SALES_FLOW_MON3` | TEXT | Third Month Total net asset value of shares sold |
| `REINVESTMENT_FLOW_MON3` | TEXT | Third Month Total net asset value of shares sold in connection with reinvestments of dividends and distributions |
| `REDEMPTION_FLOW_MON3` | TEXT | Third Month Total net asset value of shares redeemed or repurchased, including exchanges |

## `raw_fund_var_info` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `DESIGNATED_INDEX_NAME` | TEXT | For Funds subject to Relative VaR Test during the period, the name of the Fund's Designated Index, or a statement that the Fund's Designated Reference Portfolio is the Fund's Securities Portfolio |
| `DESIGNATED_INDEX_IDENTIFIER` | TEXT | The index identifier for the Fund's Designated Index. |

## `raw_fut_fwd_nonforeigncur_contract` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `PAYOFF_PROFILE` | TEXT | Payoff profile, selected from among the following (long, short). |
| `EXPIRATION_DATE` | TEXT | Expiration date. |
| `NOTIONAL_AMOUNT` | TEXT | Aggregate notional amount or contract value on trade date |
| `CURRENCY_CODE` | TEXT | Currency code |
| `UNREALIZED_APPRECIATION` | TEXT | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number. |

## `raw_fwd_foreigncur_contract_swap` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `CURRENCY_SOLD_AMOUNT` | TEXT | Amount of currency sold |
| `DESC_CURRENCY_SOLD` | TEXT | Description of currency sold |
| `CURRENCY_PURCHASED_AMOUNT` | TEXT | Amount of currency purchased. |
| `DESC_CURRENCY_PURCHASED` | TEXT | Description of currency purchased. |
| `SETTLEMENT_DATE` | TEXT | Settlement date |
| `UNREALIZED_APPRECIATION` | TEXT | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number |

## `raw_identifiers` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `IDENTIFIERS_ID` | TEXT | Surrogate Key |
| `IDENTIFIER_ISIN` | TEXT | ISIN |
| `IDENTIFIER_TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_IDENTIFIER_DESC` | TEXT | Other identifier type used |

## `raw_interest_rate_risk` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `INTEREST_RATE_RISK_ID` | TEXT | Surrogate Key |
| `CURRENCY_CODE` | TEXT | Currency code |
| `INTRST_RATE_CHANGE_3MON_DV01` | TEXT | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 3 months |
| `INTRST_RATE_CHANGE_1YR_DV01` | TEXT | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 1 year |
| `INTRST_RATE_CHANGE_5YR_DV01` | TEXT | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 5 years |
| `INTRST_RATE_CHANGE_10YR_DV01` | TEXT | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 10 years |
| `INTRST_RATE_CHANGE_30YR_DV01` | TEXT | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 30 years |
| `INTRST_RATE_CHANGE_3MON_DV100` | TEXT | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 3 months |
| `INTRST_RATE_CHANGE_1YR_DV100` | TEXT | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 1 year |
| `INTRST_RATE_CHANGE_5YR_DV100` | TEXT | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 5 years |
| `INTRST_RATE_CHANGE_10YR_DV100` | TEXT | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 10 years |
| `INTRST_RATE_CHANGE_30YR_DV100` | TEXT | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 30 years |

## `raw_monthly_return_cat_instrument` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `ASSET_CAT` | TEXT | Asset category |
| `INSTRUMENT_KIND` | TEXT | From each asset category further breakdown by derivatives instrument: forward, future, option, swaption, swap, warrant, and other |
| `NET_REALIZED_GAIN_MON1` | TEXT | First month net realized gain (loss) attributable to derivatives |
| `NET_UNREALIZED_AP_MON1` | TEXT | First month net change in unrealized appreciation (or depreciation) attributable to derivatives |
| `NET_REALIZED_GAIN_MON2` | TEXT | Second month net realized gain (loss) attributable to derivatives |
| `NET_UNREALIZED_AP_MON2` | TEXT | Second month net change in unrealized appreciation (or depreciation) attributable to derivatives |
| `NET_REALIZED_GAIN_MON3` | TEXT | Third month net realized gain (loss) attributable to derivatives |
| `NET_UNREALIZED_AP_MON3` | TEXT | Third month net change in unrealized appreciation (or depreciation) attributable to derivatives |

## `raw_monthly_total_return` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `MONTHLY_TOTAL_RETURN_ID` | TEXT | Surrogate Key |
| `CLASS_ID` | TEXT | Class identification number(s) (if any) of the Class(es) for which returns are reported. |
| `MONTHLY_TOTAL_RETURN1` | TEXT | First Month total returns of the Fund |
| `MONTHLY_TOTAL_RETURN2` | TEXT | Second Month total returns of the Fund |
| `MONTHLY_TOTAL_RETURN3` | TEXT | Third Month total returns of the Fund |

## `raw_nonforeign_exchange_swap` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `SWAP_FLAG` | TEXT | Custom swap flag |
| `TERMINATION_DATE` | TEXT | Termination or maturity date |
| `UPFRONT_PAYMENT` | TEXT | Upfront payments |
| `PMNT_CURRENCY_CODE` | TEXT | Payment currency code |
| `UPFRONT_RECEIPT` | TEXT | Upfront receipts |
| `RCPT_CURRENCY_CODE` | TEXT | Receipts currency code |
| `NOTIONAL_AMOUNT` | TEXT | Notional amount |
| `CURRENCY_CODE` | TEXT | Currency code |
| `UNREALIZED_APPRECIATION` | TEXT | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number. |
| `FIXED_OR_FLOATING_RECEIPT` | TEXT | Fixed, floating, or other receipt |
| `FIXED_RATE_RECEIPT` | TEXT | Receipt: fixed rate |
| `FLOATING_RATE_INDEX_RECEIPT` | TEXT | Receipt: floating rate index |
| `FLOATING_RATE_SPREAD_RECEIPT` | TEXT | Receipt: floating rate spread |
| `CURRENCY_CODE_RECEIPT` | TEXT | Receipt: currency code |
| `AMOUNT_RECEIPT` | TEXT | Receipt: amount |
| `FIXED_OR_FLOATING_PAYMENT` | TEXT | Fixed, floating, or other payment |
| `FIXED_RATE_PAYMENT` | TEXT | Payment: fixed rate |
| `FLOATING_RATE_INDEX_PAYMENT` | TEXT | Payment: floating rate index |
| `FLOATING_RATE_SPREAD_PAYMENT` | TEXT | Payment: floating rate spread |
| `CURRENCY_CODE_PAYMENT` | TEXT | Payment: currency code |
| `AMOUNT_PAYMENT` | TEXT | Payment: amount |

## `raw_other_deriv` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `OTHER_DESC` | TEXT | Other description |
| `TERMINATION_DATE` | TEXT | Termination date or maturity date |
| `UNREALIZED_APPRECIATION` | TEXT | Unrealized appreciation or depreciation |

## `raw_other_deriv_notional_amount` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `OTHER_DERIV_NOTIONAL_AMOUNT_ID` | TEXT | Surrogate Key |
| `NOTIONAL_AMOUNT` | TEXT | Notional amount |
| `CURRENCY_CODE` | TEXT | Currency code |

## `raw_registrant` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `CIK` | TEXT | CIK number |
| `REGISTRANT_NAME` | TEXT | Name of Registrant |
| `FILE_NUM` | TEXT | Investment Company Act file number |
| `LEI` | TEXT | LEI of Registrant |
| `ADDRESS1` | TEXT | Address line 1 |
| `ADDRESS2` | TEXT | Address line 2 |
| `CITY` | TEXT | City |
| `STATE` | TEXT | State |
| `COUNTRY` | TEXT | Country |
| `ZIP` | TEXT | Zip code |
| `PHONE` | TEXT | Phone |

## `raw_repurchase_agreement` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `TRANSACTION_TYPE` | TEXT | Category that most closely reflects the transaction (repurchase, reverse repurchase) |
| `IS_CLEARED` | TEXT | Cleared by central counterparty |
| `CENTRAL_COUNTER_PARTY` | TEXT | Name of the central counterparty |
| `IS_TRIPARTY` | TEXT | Tri-party |
| `REPURCHASE_RATE` | TEXT | Repurchase rate |
| `MATURITY_DATE` | TEXT | Maturity date |

## `raw_repurchase_collateral` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `REPURCHASE_COLLATERAL_ID` | TEXT | Surrogate Key |
| `PRINCIPAL_AMOUNT` | TEXT | Principal amount |
| `PRINCIPAL_CURRENCY_CODE` | TEXT | Principal currency code |
| `COLLATERAL_AMOUNT` | TEXT | Value of collateral |
| `COLLATERAL_CURRENCY_CODE` | TEXT | Collateral currency code |
| `INVESTMENT_CAT` | TEXT | Category of investments that most closely represents the collateral |
| `OTHER_INTRUMENT_DESC` | TEXT | Brief description if category of investment is Other Instrument |

## `raw_repurchase_counterparty` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `REPURCHASE_COUNTERPARTY_ID` | TEXT | Surrogate Key |
| `NAME` | TEXT | Name of counterparty |
| `LEI` | TEXT | LEI (if any) of counterparty |

## `raw_securities_lending` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `IS_CASH_COLLATERAL` | TEXT | Does any amount of this investment represent reinvestment of cash collateral received for loaned securities |
| `CASH_COLLATERAL_AMOUNT` | TEXT | Provide the value of the investment representing cash collateral |
| `IS_NON_CASH_COLLATERAL` | TEXT | Does any portion of this investment represent non-cash collateral that is treated as a Fund asset and received for loaned securities |
| `NON_CASH_COLLATERAL_VALUE` | TEXT | Provide the value of the securities representing non-cash collateral |
| `IS_LOAN_BY_FUND` | TEXT | Is any portion of this investment on loan by the Fund |
| `LOAN_VALUE` | TEXT | Provide the value of the securities on loan |

## `raw_submission` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `FILING_DATE` | TEXT | Filing date |
| `FILE_NUM` | TEXT | File number |
| `SUB_TYPE` | TEXT | NPORT-P, NPORT-P/A, NT NPORT-P |
| `REPORT_ENDING_PERIOD` | TEXT | Date of fiscal year-end |
| `REPORT_DATE` | TEXT | Date as of which information is reported |
| `IS_LAST_FILING` | TEXT | Does the Fund anticipate that this will be its final filing on Form N-PORT |

## `raw_swaption_option_warnt_deriv` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `PUT_OR_CALL` | TEXT | Type, selected from among the following (put, call). Respond call for warrants |
| `WRITTEN_OR_PURCHASED` | TEXT | Payoff profile, selected from among the following (written, purchased). Respond purchased for warrants |
| `SHARES_CNT` | TEXT | Number of shares of underlying reference instrument per contract |
| `PRINCIPAL_AMOUNT` | TEXT | Principal amount of underlying reference instrument per contract |
| `CURRENCY_CODE` | TEXT | Currency code |
| `EXERCISE_PRICE` | TEXT | Exercise price or rate |
| `EXPIRATION_DATE` | TEXT | Expiration date. |
| `UNREALIZED_APPRECIATION` | TEXT | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number |

## `risk_all` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `risk_row_id` | TEXT |  |
| `risk_type` | TEXT | interest_rate or credit_spread. |
| `currency` | TEXT |  |
| `credit_bucket` | TEXT | Reported INVEST or NONINVEST credit spread bucket; not a position-level rating. |
| `tenor` | TEXT | Risk bucket: 3MON, 1YR, 5YR, 10YR or 30YR. |
| `shock_bp` | INTEGER | Shock size in basis points; 1 and 100 are retained separately. |
| `value_change_usd` | REAL | Filed dollar sensitivity for the specified shock, risk category and tenor. |
| `source_column` | TEXT | Original SEC column name used to derive the normalized long risk row. |

## `schema_dictionary` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `archive_id` | TEXT |  |
| `table_name` | TEXT |  |
| `column_name` | TEXT |  |
| `source_type` | TEXT |  |
| `typed_type` | TEXT |  |
| `description` | TEXT |  |

## `settings` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `key` | TEXT |  |
| `value` | TEXT |  |

## `t_borrow_aggregate` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `BORROW_AGGREGATE_ID` | TEXT | Surrogate Key |
| `AMOUNT` | REAL | Aggregate principal amount |
| `COLLATERAL` | REAL | Aggregate value of collateral |
| `INVESTMENT_CAT` | TEXT | Category of investments |
| `OTHER_DESC` | TEXT | Brief description if category of investment is Other Instrument |

## `t_borrower` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `BORROWER_ID` | TEXT | Surrogate Key |
| `NAME` | TEXT | Name of borrower |
| `LEI` | TEXT | LEI (if any) of borrower. |
| `AGGREGATE_VALUE` | REAL | Aggregate value of all securities on loan to the borrower. |

## `t_convertible_security_currency` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `CONVERTIBLE_SECURITY_ID` | TEXT | Surrogate Key |
| `CONVERSION_RATIO` | REAL | Conversion ratio |
| `CURRENCY_CODE` | TEXT | Currency code |

## `t_debt_security` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `MATURITY_DATE` | TEXT | Maturity date |
| `COUPON_TYPE` | TEXT | The category that most closely reflects the coupon type among the following: fixed, floating, variable, none. |
| `ANNUALIZED_RATE` | REAL | Annualized rate. |
| `IS_DEFAULT` | TEXT | Currently in default |
| `ARE_ANY_INTEREST_PAYMENT` | TEXT | Are there any interest payments in arrears or have any coupon payments been legally deferred by the issuer |
| `IS_ANY_PORTION_INTEREST_PAID` | TEXT | Is any portion of the interest paid in kind? |
| `IS_CONVTIBLE_MANDATORY` | TEXT | Is it Mandatory convertible |
| `IS_CONVTIBLE_CONTINGENT` | TEXT | Is it Contingent convertible |

## `t_debt_security_ref_instrument` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DEBT_SECURITY_REF_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Name of issuer |
| `ISSUE_TITLE` | TEXT | Title of issue |
| `CURRENCY_CODE` | TEXT | Currency code |
| `CUSIP` | TEXT | CUSIP of reference instrument |
| `ISIN` | TEXT | ISIN |
| `TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_DESC` | TEXT | Type of identifier if 'other' identifier provided |

## `t_derivative_counterparty` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DERIVATIVE_COUNTERPARTY_ID` | TEXT | Surrogate Key |
| `DERIVATIVE_COUNTERPARTY_NAME` | TEXT | Name of counterparty |
| `DERIVATIVE_COUNTERPARTY_LEI` | TEXT | LEI (if any) of counterparty |

## `t_desc_ref_index_basket` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `INDEX_NAME` | TEXT | Index Name |
| `INDEX_IDENTIFIER` | TEXT | Index Identifier |
| `NARRATIVE_DESC` | TEXT | Narrative Description |

## `t_desc_ref_index_component` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DESC_REF_INDEX_COMPONENT_ID` | TEXT | Surrogate Key |
| `NAME` | TEXT | Name of component |
| `CUSIP` | TEXT | CUSIP |
| `ISIN` | TEXT | ISIN |
| `TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_DESC` | TEXT | Other identifier type used |
| `NOTIONAL_AMOUNT` | REAL | Notional amount |
| `CURRENCY_CODE` | TEXT | Currency code |
| `VALUE` | REAL | Value |
| `ISSUER_CURRENCY_CODE` | TEXT | Currency code of issuer |

## `t_desc_ref_other` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DESC_REF_OTHER_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Issuer name |
| `ISSUE_TITLE` | TEXT | Issuer title |
| `CUSIP` | TEXT | CUSIP |
| `ISIN` | TEXT | ISIN |
| `TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_DESC` | TEXT | Other identifier type used |

## `t_explanatory_note` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `EXPLANATORY_NOTE_ID` | TEXT | Surrogate Key |
| `ITEM_NO` | TEXT | Item number |
| `EXPLANATORY_NOTE` | TEXT | Explanatory note |

## `t_floating_rate_reset_tenor` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `RATE_RESET_TENOR_ID` | TEXT | Surrogate Key |
| `RECEIPT_OR_PAYMENT` | TEXT | Receipt or payment |
| `RESET_DATE` | TEXT | Rate reset date |
| `RESET_DATE_UNIT` | REAL | Rate reset unit |
| `RATE_TENOR` | TEXT | Rate tenor |
| `RATE_TENOR_UNIT` | REAL | Rate tenor unit |

## `t_fund_reported_holding` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `HOLDING_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Name of issuer |
| `ISSUER_LEI` | TEXT | LEI (if any) of issuer. In the case of a holding in a fund that is a series of a series trust, report the LEI of the series |
| `ISSUER_TITLE` | TEXT | Title of the issue or description of the investment. |
| `ISSUER_CUSIP` | TEXT | CUSIP |
| `BALANCE` | REAL | Balance |
| `UNIT` | TEXT | Indicate whether balance amount is expressed in number of shares, principal amount, or other units |
| `OTHER_UNIT_DESC` | TEXT | Other units description |
| `CURRENCY_CODE` | TEXT | Currency code |
| `CURRENCY_VALUE` | REAL | Value |
| `EXCHANGE_RATE` | REAL | Exchange rate |
| `PERCENTAGE` | REAL | Percentage value compared to net assets of the Fund |
| `PAYOFF_PROFILE` | TEXT | Payoff profile -- long, short, N/A |
| `ASSET_CAT` | TEXT | Asset type |
| `OTHER_ASSET` | TEXT | If Asset type is Other, provide a brief description. |
| `ISSUER_TYPE` | TEXT | Issuer type |
| `OTHER_ISSUER` | TEXT | If Issuer type is Other, provide a brief description. |
| `INVESTMENT_COUNTRY` | TEXT | Report the ISO country code that corresponds to the country where the issuer is organized |
| `IS_RESTRICTED_SECURITY` | TEXT | Is the investment a Restricted Security |
| `FAIR_VALUE_LEVEL` | TEXT | The level within the fair value hierarchy in which the fair value measurements fall pursuant  to US GAAP |
| `DERIVATIVE_CAT` | TEXT | Type of derivative instrument |

## `t_fund_reported_info` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `SERIES_NAME` | TEXT | Name of Series |
| `SERIES_ID` | TEXT | EDGAR Series Identifier |
| `SERIES_LEI` | TEXT | LEI of Series. |
| `TOTAL_ASSETS` | REAL | Total assets |
| `TOTAL_LIABILITIES` | REAL | Total liabilities |
| `NET_ASSETS` | REAL | Net assets |
| `ASSETS_ATTRBT_TO_MISC_SECURITY` | REAL | Assets attributable to miscellaneous securities |
| `ASSETS_INVESTED` | REAL | Assets invested in a Controlled Foreign Corporation |
| `BORROWING_PAY_WITHIN_1YR` | REAL | Amounts payable to banks or other financial institutions for borrowings within one year |
| `CTRLD_COMPANIES_PAY_WITHIN_1YR` | REAL | Amounts payable to controlled companies within one year |
| `OTHER_AFFILIA_PAY_WITHIN_1YR` | REAL | Amounts payable to other affiliates within one year |
| `OTHER_PAY_WITHIN_1YR` | REAL | Amounts payable to others within one year |
| `BORROWING_PAY_AFTER_1YR` | REAL | Amounts payable to banks or other financial institutions for borrowings after one year |
| `CTRLD_COMPANIES_PAY_AFTER_1YR` | REAL | Amounts payable to controlled companies after one year |
| `OTHER_AFFILIA_PAY_AFTER_1YR` | REAL | Amounts payable to other affiliates after one year |
| `OTHER_PAY_AFTER_1YR` | REAL | Amounts payable to others after one year |
| `DELAYED_DELIVERY` | REAL | Payables for investments purchased on a delayed delivery, when-issued, or other firm commitment basis |
| `STANDBY_COMMITMENT` | REAL | Payables for investments purchased on a standby commitment basis |
| `LIQUIDATION_PREFERENCE` | REAL | Liquidation preference of outstanding preferred stock issued by the Fund |
| `CASH_NOT_RPTD_IN_C_OR_D` | REAL | Cash and cash equivalents not reported in Parts C or D |
| `CREDIT_SPREAD_3MON_INVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 3 month maturity |
| `CREDIT_SPREAD_1YR_INVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 1 year maturity |
| `CREDIT_SPREAD_5YR_INVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 5 year maturity |
| `CREDIT_SPREAD_10YR_INVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 10 year maturity |
| `CREDIT_SPREAD_30YR_INVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 30 year maturity |
| `CREDIT_SPREAD_3MON_NONINVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 3 month maturity |
| `CREDIT_SPREAD_1YR_NONINVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 1 year maturity |
| `CREDIT_SPREAD_5YR_NONINVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 5 year maturity |
| `CREDIT_SPREAD_10YR_NONINVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 10 year maturity |
| `CREDIT_SPREAD_30YR_NONINVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 30 year maturity |
| `IS_NON_CASH_COLLATERAL` | TEXT | Did any securities lending counterparty provide any non-cash collateral |
| `NET_REALIZE_GAIN_NONDERIV_MON1` | REAL | First month net realized gain (loss) attributable to investments other than derivatives |
| `NET_UNREALIZE_AP_NONDERIV_MON1` | REAL | First month net change in unrealized appreciation (or depreciation) attributable to investments other than derivatives |
| `NET_REALIZE_GAIN_NONDERIV_MON2` | REAL | Second month net realized gain (loss) attributable to investments other than derivatives |
| `NET_UNREALIZE_AP_NONDERIV_MON2` | REAL | Second month net change in unrealized appreciation (or depreciation) attributable to investments other than derivatives |
| `NET_REALIZE_GAIN_NONDERIV_MON3` | REAL | Third month net realized gain (loss) attributable to investments other than derivatives |
| `NET_UNREALIZE_AP_NONDERIV_MON3` | REAL | Third month net change in unrealized appreciation (or depreciation) attributable to investments other than derivatives |
| `SALES_FLOW_MON1` | REAL | First Month Total net asset value of shares sold |
| `REINVESTMENT_FLOW_MON1` | REAL | First Month Total net asset value of shares sold in connection with reinvestments of dividends and distributions |
| `REDEMPTION_FLOW_MON1` | REAL | First Month Total net asset value of shares redeemed or repurchased, including exchanges |
| `SALES_FLOW_MON2` | REAL | Second Month Total net asset value of shares sold |
| `REINVESTMENT_FLOW_MON2` | REAL | Second Month Total net asset value of shares sold in connection with reinvestments of dividends and distributions |
| `REDEMPTION_FLOW_MON2` | REAL | Second Month Total net asset value of shares redeemed or repurchased, including exchanges |
| `SALES_FLOW_MON3` | REAL | Third Month Total net asset value of shares sold |
| `REINVESTMENT_FLOW_MON3` | REAL | Third Month Total net asset value of shares sold in connection with reinvestments of dividends and distributions |
| `REDEMPTION_FLOW_MON3` | REAL | Third Month Total net asset value of shares redeemed or repurchased, including exchanges |

## `t_fund_var_info` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `DESIGNATED_INDEX_NAME` | TEXT | For Funds subject to Relative VaR Test during the period, the name of the Fund's Designated Index, or a statement that the Fund's Designated Reference Portfolio is the Fund's Securities Portfolio |
| `DESIGNATED_INDEX_IDENTIFIER` | TEXT | The index identifier for the Fund's Designated Index. |

## `t_fut_fwd_nonforeigncur_contract` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `PAYOFF_PROFILE` | TEXT | Payoff profile, selected from among the following (long, short). |
| `EXPIRATION_DATE` | TEXT | Expiration date. |
| `NOTIONAL_AMOUNT` | REAL | Aggregate notional amount or contract value on trade date |
| `CURRENCY_CODE` | TEXT | Currency code |
| `UNREALIZED_APPRECIATION` | REAL | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number. |

## `t_fwd_foreigncur_contract_swap` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `CURRENCY_SOLD_AMOUNT` | REAL | Amount of currency sold |
| `DESC_CURRENCY_SOLD` | TEXT | Description of currency sold |
| `CURRENCY_PURCHASED_AMOUNT` | REAL | Amount of currency purchased. |
| `DESC_CURRENCY_PURCHASED` | TEXT | Description of currency purchased. |
| `SETTLEMENT_DATE` | TEXT | Settlement date |
| `UNREALIZED_APPRECIATION` | REAL | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number |

## `t_identifiers` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `IDENTIFIERS_ID` | TEXT | Surrogate Key |
| `IDENTIFIER_ISIN` | TEXT | ISIN |
| `IDENTIFIER_TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_IDENTIFIER_DESC` | TEXT | Other identifier type used |

## `t_interest_rate_risk` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `INTEREST_RATE_RISK_ID` | TEXT | Surrogate Key |
| `CURRENCY_CODE` | TEXT | Currency code |
| `INTRST_RATE_CHANGE_3MON_DV01` | REAL | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 3 months |
| `INTRST_RATE_CHANGE_1YR_DV01` | REAL | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 1 year |
| `INTRST_RATE_CHANGE_5YR_DV01` | REAL | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 5 years |
| `INTRST_RATE_CHANGE_10YR_DV01` | REAL | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 10 years |
| `INTRST_RATE_CHANGE_30YR_DV01` | REAL | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 30 years |
| `INTRST_RATE_CHANGE_3MON_DV100` | REAL | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 3 months |
| `INTRST_RATE_CHANGE_1YR_DV100` | REAL | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 1 year |
| `INTRST_RATE_CHANGE_5YR_DV100` | REAL | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 5 years |
| `INTRST_RATE_CHANGE_10YR_DV100` | REAL | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 10 years |
| `INTRST_RATE_CHANGE_30YR_DV100` | REAL | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 30 years |

## `t_monthly_return_cat_instrument` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `ASSET_CAT` | TEXT | Asset category |
| `INSTRUMENT_KIND` | TEXT | From each asset category further breakdown by derivatives instrument: forward, future, option, swaption, swap, warrant, and other |
| `NET_REALIZED_GAIN_MON1` | REAL | First month net realized gain (loss) attributable to derivatives |
| `NET_UNREALIZED_AP_MON1` | REAL | First month net change in unrealized appreciation (or depreciation) attributable to derivatives |
| `NET_REALIZED_GAIN_MON2` | REAL | Second month net realized gain (loss) attributable to derivatives |
| `NET_UNREALIZED_AP_MON2` | REAL | Second month net change in unrealized appreciation (or depreciation) attributable to derivatives |
| `NET_REALIZED_GAIN_MON3` | REAL | Third month net realized gain (loss) attributable to derivatives |
| `NET_UNREALIZED_AP_MON3` | REAL | Third month net change in unrealized appreciation (or depreciation) attributable to derivatives |

## `t_monthly_total_return` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `MONTHLY_TOTAL_RETURN_ID` | TEXT | Surrogate Key |
| `CLASS_ID` | TEXT | Class identification number(s) (if any) of the Class(es) for which returns are reported. |
| `MONTHLY_TOTAL_RETURN1` | REAL | First Month total returns of the Fund |
| `MONTHLY_TOTAL_RETURN2` | REAL | Second Month total returns of the Fund |
| `MONTHLY_TOTAL_RETURN3` | REAL | Third Month total returns of the Fund |

## `t_nonforeign_exchange_swap` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `SWAP_FLAG` | TEXT | Custom swap flag |
| `TERMINATION_DATE` | TEXT | Termination or maturity date |
| `UPFRONT_PAYMENT` | REAL | Upfront payments |
| `PMNT_CURRENCY_CODE` | TEXT | Payment currency code |
| `UPFRONT_RECEIPT` | REAL | Upfront receipts |
| `RCPT_CURRENCY_CODE` | TEXT | Receipts currency code |
| `NOTIONAL_AMOUNT` | REAL | Notional amount |
| `CURRENCY_CODE` | TEXT | Currency code |
| `UNREALIZED_APPRECIATION` | REAL | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number. |
| `FIXED_OR_FLOATING_RECEIPT` | TEXT | Fixed, floating, or other receipt |
| `FIXED_RATE_RECEIPT` | REAL | Receipt: fixed rate |
| `FLOATING_RATE_INDEX_RECEIPT` | TEXT | Receipt: floating rate index |
| `FLOATING_RATE_SPREAD_RECEIPT` | REAL | Receipt: floating rate spread |
| `CURRENCY_CODE_RECEIPT` | TEXT | Receipt: currency code |
| `AMOUNT_RECEIPT` | REAL | Receipt: amount |
| `FIXED_OR_FLOATING_PAYMENT` | TEXT | Fixed, floating, or other payment |
| `FIXED_RATE_PAYMENT` | REAL | Payment: fixed rate |
| `FLOATING_RATE_INDEX_PAYMENT` | TEXT | Payment: floating rate index |
| `FLOATING_RATE_SPREAD_PAYMENT` | REAL | Payment: floating rate spread |
| `CURRENCY_CODE_PAYMENT` | TEXT | Payment: currency code |
| `AMOUNT_PAYMENT` | REAL | Payment: amount |

## `t_other_deriv` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `OTHER_DESC` | TEXT | Other description |
| `TERMINATION_DATE` | TEXT | Termination date or maturity date |
| `UNREALIZED_APPRECIATION` | REAL | Unrealized appreciation or depreciation |

## `t_other_deriv_notional_amount` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `OTHER_DERIV_NOTIONAL_AMOUNT_ID` | TEXT | Surrogate Key |
| `NOTIONAL_AMOUNT` | REAL | Notional amount |
| `CURRENCY_CODE` | TEXT | Currency code |

## `t_registrant` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `CIK` | TEXT | CIK number |
| `REGISTRANT_NAME` | TEXT | Name of Registrant |
| `FILE_NUM` | TEXT | Investment Company Act file number |
| `LEI` | TEXT | LEI of Registrant |
| `ADDRESS1` | TEXT | Address line 1 |
| `ADDRESS2` | TEXT | Address line 2 |
| `CITY` | TEXT | City |
| `STATE` | TEXT | State |
| `COUNTRY` | TEXT | Country |
| `ZIP` | TEXT | Zip code |
| `PHONE` | TEXT | Phone |

## `t_repurchase_agreement` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `TRANSACTION_TYPE` | TEXT | Category that most closely reflects the transaction (repurchase, reverse repurchase) |
| `IS_CLEARED` | TEXT | Cleared by central counterparty |
| `CENTRAL_COUNTER_PARTY` | TEXT | Name of the central counterparty |
| `IS_TRIPARTY` | TEXT | Tri-party |
| `REPURCHASE_RATE` | REAL | Repurchase rate |
| `MATURITY_DATE` | TEXT | Maturity date |

## `t_repurchase_collateral` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `REPURCHASE_COLLATERAL_ID` | TEXT | Surrogate Key |
| `PRINCIPAL_AMOUNT` | REAL | Principal amount |
| `PRINCIPAL_CURRENCY_CODE` | TEXT | Principal currency code |
| `COLLATERAL_AMOUNT` | REAL | Value of collateral |
| `COLLATERAL_CURRENCY_CODE` | TEXT | Collateral currency code |
| `INVESTMENT_CAT` | TEXT | Category of investments that most closely represents the collateral |
| `OTHER_INTRUMENT_DESC` | TEXT | Brief description if category of investment is Other Instrument |

## `t_repurchase_counterparty` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `REPURCHASE_COUNTERPARTY_ID` | TEXT | Surrogate Key |
| `NAME` | TEXT | Name of counterparty |
| `LEI` | TEXT | LEI (if any) of counterparty |

## `t_securities_lending` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `IS_CASH_COLLATERAL` | TEXT | Does any amount of this investment represent reinvestment of cash collateral received for loaned securities |
| `CASH_COLLATERAL_AMOUNT` | REAL | Provide the value of the investment representing cash collateral |
| `IS_NON_CASH_COLLATERAL` | TEXT | Does any portion of this investment represent non-cash collateral that is treated as a Fund asset and received for loaned securities |
| `NON_CASH_COLLATERAL_VALUE` | REAL | Provide the value of the securities representing non-cash collateral |
| `IS_LOAN_BY_FUND` | TEXT | Is any portion of this investment on loan by the Fund |
| `LOAN_VALUE` | REAL | Provide the value of the securities on loan |

## `t_submission` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `FILING_DATE` | TEXT | Filing date |
| `FILE_NUM` | TEXT | File number |
| `SUB_TYPE` | TEXT | NPORT-P, NPORT-P/A, NT NPORT-P |
| `REPORT_ENDING_PERIOD` | TEXT | Date of fiscal year-end |
| `REPORT_DATE` | TEXT | Date as of which information is reported |
| `IS_LAST_FILING` | TEXT | Does the Fund anticipate that this will be its final filing on Form N-PORT |

## `t_swaption_option_warnt_deriv` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `PUT_OR_CALL` | TEXT | Type, selected from among the following (put, call). Respond call for warrants |
| `WRITTEN_OR_PURCHASED` | TEXT | Payoff profile, selected from among the following (written, purchased). Respond purchased for warrants |
| `SHARES_CNT` | REAL | Number of shares of underlying reference instrument per contract |
| `PRINCIPAL_AMOUNT` | REAL | Principal amount of underlying reference instrument per contract |
| `CURRENCY_CODE` | TEXT | Currency code |
| `EXERCISE_PRICE` | REAL | Exercise price or rate |
| `EXPIRATION_DATE` | TEXT | Expiration date. |
| `UNREALIZED_APPRECIATION` | REAL | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number |

## `universe` (table)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `group` | TEXT |  |
| `role` | TEXT |  |
| `style` | TEXT |  |
| `fund_name` | TEXT |  |
| `manager` | TEXT |  |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `cik` | TEXT |  |
| `ncen_is_index` | TEXT |  |
| `ncen_is_etf` | TEXT |  |
| `nport_var_reference_index` | TEXT |  |
| `prospectus_benchmark_to_verify` | TEXT |  |
| `note` | TEXT |  |

## `borrow_aggregate_latest_raw` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `fund_series_id` | TEXT |  |
| `holdings_report_date` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `BORROW_AGGREGATE_ID` | TEXT | Surrogate Key |
| `AMOUNT` | REAL | Aggregate principal amount |
| `COLLATERAL` | REAL | Aggregate value of collateral |
| `INVESTMENT_CAT` | TEXT | Category of investments |
| `OTHER_DESC` | TEXT | Brief description if category of investment is Other Instrument |

## `borrower_latest_raw` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `fund_series_id` | TEXT |  |
| `holdings_report_date` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `BORROWER_ID` | TEXT | Surrogate Key |
| `NAME` | TEXT | Name of borrower |
| `LEI` | TEXT | LEI (if any) of borrower. |
| `AGGREGATE_VALUE` | REAL | Aggregate value of all securities on loan to the borrower. |

## `convertible_security_currency_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `CONVERTIBLE_SECURITY_ID` | TEXT | Surrogate Key |
| `CONVERSION_RATIO` | REAL | Conversion ratio |
| `CURRENCY_CODE` | TEXT | Currency code |

## `coverage` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `group` | TEXT |  |
| `role` | TEXT |  |
| `style` | TEXT |  |
| `fund_name` | TEXT |  |
| `manager` | TEXT |  |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `cik` | TEXT |  |
| `ncen_is_index` | TEXT |  |
| `ncen_is_etf` | TEXT |  |
| `nport_var_reference_index` | TEXT |  |
| `prospectus_benchmark_to_verify` | TEXT |  |
| `note` | TEXT |  |
| `report_count` | expression / inherited |  |
| `first_report_date` | expression / inherited |  |
| `last_report_date` | expression / inherited |  |
| `first_filing_date` | expression / inherited |  |
| `last_filing_date` | expression / inherited |  |
| `coverage_status` | expression / inherited |  |

## `coverage_gaps` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `previous_report_date` | expression / inherited |  |
| `gap_days` | expression / inherited |  |

## `debt_security_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `MATURITY_DATE` | TEXT | Maturity date |
| `COUPON_TYPE` | TEXT | The category that most closely reflects the coupon type among the following: fixed, floating, variable, none. |
| `ANNUALIZED_RATE` | REAL | Annualized rate. |
| `IS_DEFAULT` | TEXT | Currently in default |
| `ARE_ANY_INTEREST_PAYMENT` | TEXT | Are there any interest payments in arrears or have any coupon payments been legally deferred by the issuer |
| `IS_ANY_PORTION_INTEREST_PAID` | TEXT | Is any portion of the interest paid in kind? |
| `IS_CONVTIBLE_MANDATORY` | TEXT | Is it Mandatory convertible |
| `IS_CONVTIBLE_CONTINGENT` | TEXT | Is it Contingent convertible |

## `debt_security_ref_instrument_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DEBT_SECURITY_REF_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Name of issuer |
| `ISSUE_TITLE` | TEXT | Title of issue |
| `CURRENCY_CODE` | TEXT | Currency code |
| `CUSIP` | TEXT | CUSIP of reference instrument |
| `ISIN` | TEXT | ISIN |
| `TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_DESC` | TEXT | Type of identifier if 'other' identifier provided |

## `debt_unique` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT |  |
| `MATURITY_DATE` | TEXT |  |
| `COUPON_TYPE` | TEXT |  |
| `ANNUALIZED_RATE` | REAL |  |
| `IS_DEFAULT` | TEXT |  |
| `ARE_ANY_INTEREST_PAYMENT` | TEXT |  |
| `IS_ANY_PORTION_INTEREST_PAID` | TEXT |  |
| `IS_CONVTIBLE_MANDATORY` | TEXT |  |
| `IS_CONVTIBLE_CONTINGENT` | TEXT |  |

## `derivative_counterparty_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DERIVATIVE_COUNTERPARTY_ID` | TEXT | Surrogate Key |
| `DERIVATIVE_COUNTERPARTY_NAME` | TEXT | Name of counterparty |
| `DERIVATIVE_COUNTERPARTY_LEI` | TEXT | LEI (if any) of counterparty |

## `derivative_pnl` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `month_end` | TEXT | Calendar month-end associated with the monthly observation. |
| `asset_category` | TEXT |  |
| `instrument_kind` | TEXT |  |
| `month_slot` | INTEGER | Source month slot: 1 oldest, 3 newest, anchored to report month. |
| `realized_pnl_usd` | REAL |  |
| `unrealized_change_usd` | REAL |  |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |

## `derivative_pnl_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `month_end` | TEXT | Calendar month-end associated with the monthly observation. |
| `asset_category` | TEXT |  |
| `instrument_kind` | TEXT |  |
| `month_slot` | INTEGER | Source month slot: 1 oldest, 3 newest, anchored to report month. |
| `realized_pnl_usd` | REAL |  |
| `unrealized_change_usd` | REAL |  |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |

## `desc_ref_index_basket_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `INDEX_NAME` | TEXT | Index Name |
| `INDEX_IDENTIFIER` | TEXT | Index Identifier |
| `NARRATIVE_DESC` | TEXT | Narrative Description |

## `desc_ref_index_component_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DESC_REF_INDEX_COMPONENT_ID` | TEXT | Surrogate Key |
| `NAME` | TEXT | Name of component |
| `CUSIP` | TEXT | CUSIP |
| `ISIN` | TEXT | ISIN |
| `TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_DESC` | TEXT | Other identifier type used |
| `NOTIONAL_AMOUNT` | REAL | Notional amount |
| `CURRENCY_CODE` | TEXT | Currency code |
| `VALUE` | REAL | Value |
| `ISSUER_CURRENCY_CODE` | TEXT | Currency code of issuer |

## `desc_ref_other_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `DESC_REF_OTHER_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Issuer name |
| `ISSUE_TITLE` | TEXT | Issuer title |
| `CUSIP` | TEXT | CUSIP |
| `ISIN` | TEXT | ISIN |
| `TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_DESC` | TEXT | Other identifier type used |

## `explanatory_note_latest_raw` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `fund_series_id` | TEXT |  |
| `holdings_report_date` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `EXPLANATORY_NOTE_ID` | TEXT | Surrogate Key |
| `ITEM_NO` | TEXT | Item number |
| `EXPLANATORY_NOTE` | TEXT | Explanatory note |

## `filings` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `cik` | TEXT |  |
| `series_name` | TEXT |  |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `report_month` | TEXT | Report date aligned to calendar month-end; the exact report_date is retained. |
| `fiscal_year_end` | TEXT |  |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `submission_type` | TEXT |  |
| `is_last_filing` | TEXT |  |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |
| `total_assets` | REAL |  |
| `total_liabilities` | REAL |  |
| `net_assets` | REAL |  |
| `archive_copy_rank` | expression / inherited | Canonical archive-copy selection rank; 1 is selected. |

## `filings_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `cik` | TEXT |  |
| `series_name` | TEXT |  |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `report_month` | TEXT | Report date aligned to calendar month-end; the exact report_date is retained. |
| `fiscal_year_end` | TEXT |  |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `submission_type` | TEXT |  |
| `is_last_filing` | TEXT |  |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |
| `total_assets` | REAL |  |
| `total_liabilities` | REAL |  |
| `net_assets` | REAL |  |
| `archive_copy_rank` | expression / inherited | Canonical archive-copy selection rank; 1 is selected. |
| `amendment_rank` | expression / inherited | Latest filing selection rank within fund/exact report date; 1 is selected. |

## `floating_rate_reset_tenor_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `RATE_RESET_TENOR_ID` | TEXT | Surrogate Key |
| `RECEIPT_OR_PAYMENT` | TEXT | Receipt or payment |
| `RESET_DATE` | TEXT | Rate reset date |
| `RESET_DATE_UNIT` | REAL | Rate reset unit |
| `RATE_TENOR` | TEXT | Rate tenor |
| `RATE_TENOR_UNIT` | REAL | Rate tenor unit |

## `fund_quarter` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `cik` | TEXT |  |
| `series_name` | TEXT |  |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `report_month` | TEXT | Report date aligned to calendar month-end; the exact report_date is retained. |
| `fiscal_year_end` | TEXT |  |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `submission_type` | TEXT |  |
| `is_last_filing` | TEXT |  |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |
| `total_assets` | REAL |  |
| `total_liabilities` | REAL |  |
| `net_assets` | REAL |  |
| `archive_copy_rank` | expression / inherited | Canonical archive-copy selection rank; 1 is selected. |
| `amendment_rank` | expression / inherited | Latest filing selection rank within fund/exact report date; 1 is selected. |
| `fund_name` | TEXT |  |
| `universe_group` | TEXT |  |
| `role` | TEXT |  |
| `style` | TEXT |  |
| `manager` | TEXT |  |
| `delayed_delivery_payables_usd` | REAL | Payables for delayed-delivery purchases from fund reported information. |
| `cash_not_in_holdings_usd` | REAL | Reported cash not included in the holdings sections; unavailable is not assumed zero. |
| `filing_lag_days` | expression / inherited | Calendar days between report date and filing date. |
| `usd_rate_sensitivity_years_signed` | expression / inherited | Sum of all five complete USD DV01 tenor sensitivities, normalized by net assets. Filed sign retained. |
| `ig_spread_sensitivity_years_signed` | expression / inherited | Complete reported investment-grade spread sensitivity, normalized to signed years. Cross-family conventions unverified. |
| `hy_spread_sensitivity_years_signed` | expression / inherited | Complete reported non-investment-grade spread sensitivity, normalized to signed years. |

## `fund_reported_info_latest_raw` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `fund_series_id` | TEXT |  |
| `holdings_report_date` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `SERIES_NAME` | TEXT | Name of Series |
| `SERIES_ID` | TEXT | EDGAR Series Identifier |
| `SERIES_LEI` | TEXT | LEI of Series. |
| `TOTAL_ASSETS` | REAL | Total assets |
| `TOTAL_LIABILITIES` | REAL | Total liabilities |
| `NET_ASSETS` | REAL | Net assets |
| `ASSETS_ATTRBT_TO_MISC_SECURITY` | REAL | Assets attributable to miscellaneous securities |
| `ASSETS_INVESTED` | REAL | Assets invested in a Controlled Foreign Corporation |
| `BORROWING_PAY_WITHIN_1YR` | REAL | Amounts payable to banks or other financial institutions for borrowings within one year |
| `CTRLD_COMPANIES_PAY_WITHIN_1YR` | REAL | Amounts payable to controlled companies within one year |
| `OTHER_AFFILIA_PAY_WITHIN_1YR` | REAL | Amounts payable to other affiliates within one year |
| `OTHER_PAY_WITHIN_1YR` | REAL | Amounts payable to others within one year |
| `BORROWING_PAY_AFTER_1YR` | REAL | Amounts payable to banks or other financial institutions for borrowings after one year |
| `CTRLD_COMPANIES_PAY_AFTER_1YR` | REAL | Amounts payable to controlled companies after one year |
| `OTHER_AFFILIA_PAY_AFTER_1YR` | REAL | Amounts payable to other affiliates after one year |
| `OTHER_PAY_AFTER_1YR` | REAL | Amounts payable to others after one year |
| `DELAYED_DELIVERY` | REAL | Payables for investments purchased on a delayed delivery, when-issued, or other firm commitment basis |
| `STANDBY_COMMITMENT` | REAL | Payables for investments purchased on a standby commitment basis |
| `LIQUIDATION_PREFERENCE` | REAL | Liquidation preference of outstanding preferred stock issued by the Fund |
| `CASH_NOT_RPTD_IN_C_OR_D` | REAL | Cash and cash equivalents not reported in Parts C or D |
| `CREDIT_SPREAD_3MON_INVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 3 month maturity |
| `CREDIT_SPREAD_1YR_INVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 1 year maturity |
| `CREDIT_SPREAD_5YR_INVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 5 year maturity |
| `CREDIT_SPREAD_10YR_INVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 10 year maturity |
| `CREDIT_SPREAD_30YR_INVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by investment grade for 30 year maturity |
| `CREDIT_SPREAD_3MON_NONINVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 3 month maturity |
| `CREDIT_SPREAD_1YR_NONINVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 1 year maturity |
| `CREDIT_SPREAD_5YR_NONINVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 5 year maturity |
| `CREDIT_SPREAD_10YR_NONINVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 10 year maturity |
| `CREDIT_SPREAD_30YR_NONINVEST` | REAL | The change in value of the portfolio resulting from a 1 basis point change in credit spreads where the shift is applied to the option adjusted spread, aggregated by non investment grade for 30 year maturity |
| `IS_NON_CASH_COLLATERAL` | TEXT | Did any securities lending counterparty provide any non-cash collateral |
| `NET_REALIZE_GAIN_NONDERIV_MON1` | REAL | First month net realized gain (loss) attributable to investments other than derivatives |
| `NET_UNREALIZE_AP_NONDERIV_MON1` | REAL | First month net change in unrealized appreciation (or depreciation) attributable to investments other than derivatives |
| `NET_REALIZE_GAIN_NONDERIV_MON2` | REAL | Second month net realized gain (loss) attributable to investments other than derivatives |
| `NET_UNREALIZE_AP_NONDERIV_MON2` | REAL | Second month net change in unrealized appreciation (or depreciation) attributable to investments other than derivatives |
| `NET_REALIZE_GAIN_NONDERIV_MON3` | REAL | Third month net realized gain (loss) attributable to investments other than derivatives |
| `NET_UNREALIZE_AP_NONDERIV_MON3` | REAL | Third month net change in unrealized appreciation (or depreciation) attributable to investments other than derivatives |
| `SALES_FLOW_MON1` | REAL | First Month Total net asset value of shares sold |
| `REINVESTMENT_FLOW_MON1` | REAL | First Month Total net asset value of shares sold in connection with reinvestments of dividends and distributions |
| `REDEMPTION_FLOW_MON1` | REAL | First Month Total net asset value of shares redeemed or repurchased, including exchanges |
| `SALES_FLOW_MON2` | REAL | Second Month Total net asset value of shares sold |
| `REINVESTMENT_FLOW_MON2` | REAL | Second Month Total net asset value of shares sold in connection with reinvestments of dividends and distributions |
| `REDEMPTION_FLOW_MON2` | REAL | Second Month Total net asset value of shares redeemed or repurchased, including exchanges |
| `SALES_FLOW_MON3` | REAL | Third Month Total net asset value of shares sold |
| `REINVESTMENT_FLOW_MON3` | REAL | Third Month Total net asset value of shares sold in connection with reinvestments of dividends and distributions |
| `REDEMPTION_FLOW_MON3` | REAL | Third Month Total net asset value of shares redeemed or repurchased, including exchanges |

## `fund_snapshots` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `cik` | TEXT |  |
| `series_name` | TEXT |  |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `report_month` | TEXT | Report date aligned to calendar month-end; the exact report_date is retained. |
| `fiscal_year_end` | TEXT |  |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `submission_type` | TEXT |  |
| `is_last_filing` | TEXT |  |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |
| `total_assets` | REAL |  |
| `total_liabilities` | REAL |  |
| `net_assets` | REAL |  |
| `archive_copy_rank` | expression / inherited | Canonical archive-copy selection rank; 1 is selected. |
| `amendment_rank` | expression / inherited | Latest filing selection rank within fund/exact report date; 1 is selected. |
| `fund_name` | TEXT |  |
| `universe_group` | TEXT |  |
| `role` | TEXT |  |
| `style` | TEXT |  |
| `manager` | TEXT |  |

## `fund_var_info_latest_raw` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `fund_series_id` | TEXT |  |
| `holdings_report_date` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `DESIGNATED_INDEX_NAME` | TEXT | For Funds subject to Relative VaR Test during the period, the name of the Fund's Designated Index, or a statement that the Fund's Designated Reference Portfolio is the Fund's Securities Portfolio |
| `DESIGNATED_INDEX_IDENTIFIER` | TEXT | The index identifier for the Fund's Designated Index. |

## `fut_fwd_nonforeigncur_contract_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `PAYOFF_PROFILE` | TEXT | Payoff profile, selected from among the following (long, short). |
| `EXPIRATION_DATE` | TEXT | Expiration date. |
| `NOTIONAL_AMOUNT` | REAL | Aggregate notional amount or contract value on trade date |
| `CURRENCY_CODE` | TEXT | Currency code |
| `UNREALIZED_APPRECIATION` | REAL | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number. |

## `fwd_foreigncur_contract_swap_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `CURRENCY_SOLD_AMOUNT` | REAL | Amount of currency sold |
| `DESC_CURRENCY_SOLD` | TEXT | Description of currency sold |
| `CURRENCY_PURCHASED_AMOUNT` | REAL | Amount of currency purchased. |
| `DESC_CURRENCY_PURCHASED` | TEXT | Description of currency purchased. |
| `SETTLEMENT_DATE` | TEXT | Settlement date |
| `UNREALIZED_APPRECIATION` | REAL | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number |

## `holdings_all` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `report_month` | TEXT | Report date aligned to calendar month-end; the exact report_date is retained. |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `HOLDING_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Name of issuer |
| `ISSUER_LEI` | TEXT | LEI (if any) of issuer. In the case of a holding in a fund that is a series of a series trust, report the LEI of the series |
| `ISSUER_TITLE` | TEXT | Title of the issue or description of the investment. |
| `ISSUER_CUSIP` | TEXT | CUSIP |
| `BALANCE` | REAL | Balance |
| `UNIT` | TEXT | Indicate whether balance amount is expressed in number of shares, principal amount, or other units |
| `OTHER_UNIT_DESC` | TEXT | Other units description |
| `CURRENCY_CODE` | TEXT | Currency code |
| `CURRENCY_VALUE` | REAL | Value |
| `EXCHANGE_RATE` | REAL | Exchange rate |
| `PERCENTAGE` | REAL | Percentage value compared to net assets of the Fund |
| `PAYOFF_PROFILE` | TEXT | Payoff profile -- long, short, N/A |
| `ASSET_CAT` | TEXT | Asset type |
| `OTHER_ASSET` | TEXT | If Asset type is Other, provide a brief description. |
| `ISSUER_TYPE` | TEXT | Issuer type |
| `OTHER_ISSUER` | TEXT | If Issuer type is Other, provide a brief description. |
| `INVESTMENT_COUNTRY` | TEXT | Report the ISO country code that corresponds to the country where the issuer is organized |
| `IS_RESTRICTED_SECURITY` | TEXT | Is the investment a Restricted Security |
| `FAIR_VALUE_LEVEL` | TEXT | The level within the fair value hierarchy in which the fair value measurements fall pursuant  to US GAAP |
| `DERIVATIVE_CAT` | TEXT | Type of derivative instrument |
| `weight_fraction` | expression / inherited | Reported PERCENTAGE divided by 100; not renormalized. |

## `holdings_checks` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `ACCESSION_NUMBER` | TEXT |  |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `holding_count` | expression / inherited |  |
| `reported_weight_sum_pct` | expression / inherited |  |
| `missing_cusip_count` | expression / inherited |  |
| `missing_weight_count` | expression / inherited |  |

## `holdings_enriched_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `report_month` | TEXT | Report date aligned to calendar month-end; the exact report_date is retained. |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `HOLDING_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Name of issuer |
| `ISSUER_LEI` | TEXT | LEI (if any) of issuer. In the case of a holding in a fund that is a series of a series trust, report the LEI of the series |
| `ISSUER_TITLE` | TEXT | Title of the issue or description of the investment. |
| `ISSUER_CUSIP` | TEXT | CUSIP |
| `BALANCE` | REAL | Balance |
| `UNIT` | TEXT | Indicate whether balance amount is expressed in number of shares, principal amount, or other units |
| `OTHER_UNIT_DESC` | TEXT | Other units description |
| `CURRENCY_CODE` | TEXT | Currency code |
| `CURRENCY_VALUE` | REAL | Value |
| `EXCHANGE_RATE` | REAL | Exchange rate |
| `PERCENTAGE` | REAL | Percentage value compared to net assets of the Fund |
| `PAYOFF_PROFILE` | TEXT | Payoff profile -- long, short, N/A |
| `ASSET_CAT` | TEXT | Asset type |
| `OTHER_ASSET` | TEXT | If Asset type is Other, provide a brief description. |
| `ISSUER_TYPE` | TEXT | Issuer type |
| `OTHER_ISSUER` | TEXT | If Issuer type is Other, provide a brief description. |
| `INVESTMENT_COUNTRY` | TEXT | Report the ISO country code that corresponds to the country where the issuer is organized |
| `IS_RESTRICTED_SECURITY` | TEXT | Is the investment a Restricted Security |
| `FAIR_VALUE_LEVEL` | TEXT | The level within the fair value hierarchy in which the fair value measurements fall pursuant  to US GAAP |
| `DERIVATIVE_CAT` | TEXT | Type of derivative instrument |
| `weight_fraction` | expression / inherited | Reported PERCENTAGE divided by 100; not renormalized. |
| `is_reported_derivative` | expression / inherited | Indicator derived from the SEC derivative category; not a TBA detector. |
| `MATURITY_DATE` | TEXT |  |
| `COUPON_TYPE` | TEXT |  |
| `coupon_pct` | REAL | Annualized coupon rate in percent from an unambiguous debt child row. |
| `coupon_decimal` | expression / inherited | Annualized coupon_pct divided by 100. |
| `IS_DEFAULT` | TEXT |  |
| `years_to_maturity` | expression / inherited | Remaining years from report date to reported maturity, from an unambiguous debt child row. |

## `holdings_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `report_month` | TEXT | Report date aligned to calendar month-end; the exact report_date is retained. |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `HOLDING_ID` | TEXT | Surrogate Key |
| `ISSUER_NAME` | TEXT | Name of issuer |
| `ISSUER_LEI` | TEXT | LEI (if any) of issuer. In the case of a holding in a fund that is a series of a series trust, report the LEI of the series |
| `ISSUER_TITLE` | TEXT | Title of the issue or description of the investment. |
| `ISSUER_CUSIP` | TEXT | CUSIP |
| `BALANCE` | REAL | Balance |
| `UNIT` | TEXT | Indicate whether balance amount is expressed in number of shares, principal amount, or other units |
| `OTHER_UNIT_DESC` | TEXT | Other units description |
| `CURRENCY_CODE` | TEXT | Currency code |
| `CURRENCY_VALUE` | REAL | Value |
| `EXCHANGE_RATE` | REAL | Exchange rate |
| `PERCENTAGE` | REAL | Percentage value compared to net assets of the Fund |
| `PAYOFF_PROFILE` | TEXT | Payoff profile -- long, short, N/A |
| `ASSET_CAT` | TEXT | Asset type |
| `OTHER_ASSET` | TEXT | If Asset type is Other, provide a brief description. |
| `ISSUER_TYPE` | TEXT | Issuer type |
| `OTHER_ISSUER` | TEXT | If Issuer type is Other, provide a brief description. |
| `INVESTMENT_COUNTRY` | TEXT | Report the ISO country code that corresponds to the country where the issuer is organized |
| `IS_RESTRICTED_SECURITY` | TEXT | Is the investment a Restricted Security |
| `FAIR_VALUE_LEVEL` | TEXT | The level within the fair value hierarchy in which the fair value measurements fall pursuant  to US GAAP |
| `DERIVATIVE_CAT` | TEXT | Type of derivative instrument |
| `weight_fraction` | expression / inherited | Reported PERCENTAGE divided by 100; not renormalized. |

## `identifiers_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `IDENTIFIERS_ID` | TEXT | Surrogate Key |
| `IDENTIFIER_ISIN` | TEXT | ISIN |
| `IDENTIFIER_TICKER` | TEXT | Ticker |
| `OTHER_IDENTIFIER` | TEXT | Other identifier |
| `OTHER_IDENTIFIER_DESC` | TEXT | Other identifier type used |

## `interest_rate_risk_latest_raw` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `fund_series_id` | TEXT |  |
| `holdings_report_date` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `INTEREST_RATE_RISK_ID` | TEXT | Surrogate Key |
| `CURRENCY_CODE` | TEXT | Currency code |
| `INTRST_RATE_CHANGE_3MON_DV01` | REAL | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 3 months |
| `INTRST_RATE_CHANGE_1YR_DV01` | REAL | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 1 year |
| `INTRST_RATE_CHANGE_5YR_DV01` | REAL | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 5 years |
| `INTRST_RATE_CHANGE_10YR_DV01` | REAL | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 10 years |
| `INTRST_RATE_CHANGE_30YR_DV01` | REAL | Change in value of the portfolio resulting from a 1 basis point change in interest rates for maturity in 30 years |
| `INTRST_RATE_CHANGE_3MON_DV100` | REAL | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 3 months |
| `INTRST_RATE_CHANGE_1YR_DV100` | REAL | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 1 year |
| `INTRST_RATE_CHANGE_5YR_DV100` | REAL | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 5 years |
| `INTRST_RATE_CHANGE_10YR_DV100` | REAL | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 10 years |
| `INTRST_RATE_CHANGE_30YR_DV100` | REAL | Change in value of the portfolio resulting from a 100 basis point change in interest rates for maturity in 30 years |

## `monthly_flows` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `month_end` | TEXT | Calendar month-end associated with the monthly observation. |
| `month_slot` | INTEGER | Source month slot: 1 oldest, 3 newest, anchored to report month. |
| `sales_usd` | REAL |  |
| `reinvestment_usd` | REAL |  |
| `redemptions_usd` | REAL |  |
| `net_external_flow_usd` | REAL | sales_usd minus redemptions_usd; excludes reinvestment. |
| `net_flow_including_reinvestment_usd` | REAL | sales_usd + reinvestment_usd - redemptions_usd. |
| `nonderivative_realized_pnl_usd` | REAL |  |
| `nonderivative_unrealized_change_usd` | REAL |  |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |

## `monthly_flows_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `month_end` | TEXT | Calendar month-end associated with the monthly observation. |
| `month_slot` | INTEGER | Source month slot: 1 oldest, 3 newest, anchored to report month. |
| `sales_usd` | REAL |  |
| `reinvestment_usd` | REAL |  |
| `redemptions_usd` | REAL |  |
| `net_external_flow_usd` | REAL | sales_usd minus redemptions_usd; excludes reinvestment. |
| `net_flow_including_reinvestment_usd` | REAL | sales_usd + reinvestment_usd - redemptions_usd. |
| `nonderivative_realized_pnl_usd` | REAL |  |
| `nonderivative_unrealized_change_usd` | REAL |  |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |

## `monthly_return_cat_instrument_latest_raw` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `fund_series_id` | TEXT |  |
| `holdings_report_date` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `ASSET_CAT` | TEXT | Asset category |
| `INSTRUMENT_KIND` | TEXT | From each asset category further breakdown by derivatives instrument: forward, future, option, swaption, swap, warrant, and other |
| `NET_REALIZED_GAIN_MON1` | REAL | First month net realized gain (loss) attributable to derivatives |
| `NET_UNREALIZED_AP_MON1` | REAL | First month net change in unrealized appreciation (or depreciation) attributable to derivatives |
| `NET_REALIZED_GAIN_MON2` | REAL | Second month net realized gain (loss) attributable to derivatives |
| `NET_UNREALIZED_AP_MON2` | REAL | Second month net change in unrealized appreciation (or depreciation) attributable to derivatives |
| `NET_REALIZED_GAIN_MON3` | REAL | Third month net realized gain (loss) attributable to derivatives |
| `NET_UNREALIZED_AP_MON3` | REAL | Third month net change in unrealized appreciation (or depreciation) attributable to derivatives |

## `monthly_returns` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `month_end` | TEXT | Calendar month-end associated with the monthly observation. |
| `return_row_id` | TEXT |  |
| `class_id` | TEXT |  |
| `month_slot` | INTEGER | Source month slot: 1 oldest, 3 newest, anchored to report month. |
| `return_pct` | REAL | Monthly share-class return in percentage points: 1.25 means 1.25%. |
| `return_decimal` | REAL | Monthly share-class return as a decimal: 0.0125 means 1.25%. |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |

## `monthly_returns_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `month_end` | TEXT | Calendar month-end associated with the monthly observation. |
| `return_row_id` | TEXT |  |
| `class_id` | TEXT |  |
| `month_slot` | INTEGER | Source month slot: 1 oldest, 3 newest, anchored to report month. |
| `return_pct` | REAL | Monthly share-class return in percentage points: 1.25 means 1.25%. |
| `return_decimal` | REAL | Monthly share-class return as a decimal: 0.0125 means 1.25%. |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |

## `monthly_total_return_latest_raw` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `fund_series_id` | TEXT |  |
| `holdings_report_date` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `MONTHLY_TOTAL_RETURN_ID` | TEXT | Surrogate Key |
| `CLASS_ID` | TEXT | Class identification number(s) (if any) of the Class(es) for which returns are reported. |
| `MONTHLY_TOTAL_RETURN1` | REAL | First Month total returns of the Fund |
| `MONTHLY_TOTAL_RETURN2` | REAL | Second Month total returns of the Fund |
| `MONTHLY_TOTAL_RETURN3` | REAL | Third Month total returns of the Fund |

## `nonforeign_exchange_swap_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `SWAP_FLAG` | TEXT | Custom swap flag |
| `TERMINATION_DATE` | TEXT | Termination or maturity date |
| `UPFRONT_PAYMENT` | REAL | Upfront payments |
| `PMNT_CURRENCY_CODE` | TEXT | Payment currency code |
| `UPFRONT_RECEIPT` | REAL | Upfront receipts |
| `RCPT_CURRENCY_CODE` | TEXT | Receipts currency code |
| `NOTIONAL_AMOUNT` | REAL | Notional amount |
| `CURRENCY_CODE` | TEXT | Currency code |
| `UNREALIZED_APPRECIATION` | REAL | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number. |
| `FIXED_OR_FLOATING_RECEIPT` | TEXT | Fixed, floating, or other receipt |
| `FIXED_RATE_RECEIPT` | REAL | Receipt: fixed rate |
| `FLOATING_RATE_INDEX_RECEIPT` | TEXT | Receipt: floating rate index |
| `FLOATING_RATE_SPREAD_RECEIPT` | REAL | Receipt: floating rate spread |
| `CURRENCY_CODE_RECEIPT` | TEXT | Receipt: currency code |
| `AMOUNT_RECEIPT` | REAL | Receipt: amount |
| `FIXED_OR_FLOATING_PAYMENT` | TEXT | Fixed, floating, or other payment |
| `FIXED_RATE_PAYMENT` | REAL | Payment: fixed rate |
| `FLOATING_RATE_INDEX_PAYMENT` | TEXT | Payment: floating rate index |
| `FLOATING_RATE_SPREAD_PAYMENT` | REAL | Payment: floating rate spread |
| `CURRENCY_CODE_PAYMENT` | TEXT | Payment: currency code |
| `AMOUNT_PAYMENT` | REAL | Payment: amount |

## `other_deriv_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `OTHER_DESC` | TEXT | Other description |
| `TERMINATION_DATE` | TEXT | Termination date or maturity date |
| `UNREALIZED_APPRECIATION` | REAL | Unrealized appreciation or depreciation |

## `other_deriv_notional_amount_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `OTHER_DERIV_NOTIONAL_AMOUNT_ID` | TEXT | Surrogate Key |
| `NOTIONAL_AMOUNT` | REAL | Notional amount |
| `CURRENCY_CODE` | TEXT | Currency code |

## `registrant_latest_raw` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `fund_series_id` | TEXT |  |
| `holdings_report_date` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `CIK` | TEXT | CIK number |
| `REGISTRANT_NAME` | TEXT | Name of Registrant |
| `FILE_NUM` | TEXT | Investment Company Act file number |
| `LEI` | TEXT | LEI of Registrant |
| `ADDRESS1` | TEXT | Address line 1 |
| `ADDRESS2` | TEXT | Address line 2 |
| `CITY` | TEXT | City |
| `STATE` | TEXT | State |
| `COUNTRY` | TEXT | Country |
| `ZIP` | TEXT | Zip code |
| `PHONE` | TEXT | Phone |

## `repurchase_agreement_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `TRANSACTION_TYPE` | TEXT | Category that most closely reflects the transaction (repurchase, reverse repurchase) |
| `IS_CLEARED` | TEXT | Cleared by central counterparty |
| `CENTRAL_COUNTER_PARTY` | TEXT | Name of the central counterparty |
| `IS_TRIPARTY` | TEXT | Tri-party |
| `REPURCHASE_RATE` | REAL | Repurchase rate |
| `MATURITY_DATE` | TEXT | Maturity date |

## `repurchase_collateral_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `REPURCHASE_COLLATERAL_ID` | TEXT | Surrogate Key |
| `PRINCIPAL_AMOUNT` | REAL | Principal amount |
| `PRINCIPAL_CURRENCY_CODE` | TEXT | Principal currency code |
| `COLLATERAL_AMOUNT` | REAL | Value of collateral |
| `COLLATERAL_CURRENCY_CODE` | TEXT | Collateral currency code |
| `INVESTMENT_CAT` | TEXT | Category of investments that most closely represents the collateral |
| `OTHER_INTRUMENT_DESC` | TEXT | Brief description if category of investment is Other Instrument |

## `repurchase_counterparty_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `REPURCHASE_COUNTERPARTY_ID` | TEXT | Surrogate Key |
| `NAME` | TEXT | Name of counterparty |
| `LEI` | TEXT | LEI (if any) of counterparty |

## `risk` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `risk_row_id` | TEXT |  |
| `risk_type` | TEXT | interest_rate or credit_spread. |
| `currency` | TEXT |  |
| `credit_bucket` | TEXT | Reported INVEST or NONINVEST credit spread bucket; not a position-level rating. |
| `tenor` | TEXT | Risk bucket: 3MON, 1YR, 5YR, 10YR or 30YR. |
| `shock_bp` | INTEGER | Shock size in basis points; 1 and 100 are retained separately. |
| `value_change_usd` | REAL | Filed dollar sensitivity for the specified shock, risk category and tenor. |
| `source_column` | TEXT | Original SEC column name used to derive the normalized long risk row. |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |

## `risk_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `risk_row_id` | TEXT |  |
| `risk_type` | TEXT | interest_rate or credit_spread. |
| `currency` | TEXT |  |
| `credit_bucket` | TEXT | Reported INVEST or NONINVEST credit spread bucket; not a position-level rating. |
| `tenor` | TEXT | Risk bucket: 3MON, 1YR, 5YR, 10YR or 30YR. |
| `shock_bp` | INTEGER | Shock size in basis points; 1 and 100 are retained separately. |
| `value_change_usd` | REAL | Filed dollar sensitivity for the specified shock, risk category and tenor. |
| `source_column` | TEXT | Original SEC column name used to derive the normalized long risk row. |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |

## `risk_normalized_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `risk_row_id` | TEXT |  |
| `risk_type` | TEXT | interest_rate or credit_spread. |
| `currency` | TEXT |  |
| `credit_bucket` | TEXT | Reported INVEST or NONINVEST credit spread bucket; not a position-level rating. |
| `tenor` | TEXT | Risk bucket: 3MON, 1YR, 5YR, 10YR or 30YR. |
| `shock_bp` | INTEGER | Shock size in basis points; 1 and 100 are retained separately. |
| `value_change_usd` | REAL | Filed dollar sensitivity for the specified shock, risk category and tenor. |
| `source_column` | TEXT | Original SEC column name used to derive the normalized long risk row. |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |
| `net_assets` | REAL |  |
| `reported_sensitivity_years` | expression / inherited | For 1-bp shocks and positive net assets: filed value_change_usd * 10,000 / net_assets. Filed sign retained. |

## `risk_review_flags` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `cik` | TEXT |  |
| `series_name` | TEXT |  |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `report_month` | TEXT | Report date aligned to calendar month-end; the exact report_date is retained. |
| `fiscal_year_end` | TEXT |  |
| `filing_date` | TEXT | Submission date; not independently verified public dissemination time. |
| `submission_type` | TEXT |  |
| `is_last_filing` | TEXT |  |
| `available_date_assumed` | TEXT | Default: max(filing_date, report_date + 60 calendar days) + 1 day. Unverified research proxy. |
| `availability_basis` | TEXT | Description of the assumed or overridden availability convention. |
| `total_assets` | REAL |  |
| `total_liabilities` | REAL |  |
| `net_assets` | REAL |  |
| `archive_copy_rank` | expression / inherited | Canonical archive-copy selection rank; 1 is selected. |
| `amendment_rank` | expression / inherited | Latest filing selection rank within fund/exact report date; 1 is selected. |
| `fund_name` | TEXT |  |
| `universe_group` | TEXT |  |
| `role` | TEXT |  |
| `style` | TEXT |  |
| `manager` | TEXT |  |
| `delayed_delivery_payables_usd` | REAL | Payables for delayed-delivery purchases from fund reported information. |
| `cash_not_in_holdings_usd` | REAL | Reported cash not included in the holdings sections; unavailable is not assumed zero. |
| `filing_lag_days` | expression / inherited | Calendar days between report date and filing date. |
| `usd_rate_sensitivity_years_signed` | expression / inherited | Sum of all five complete USD DV01 tenor sensitivities, normalized by net assets. Filed sign retained. |
| `ig_spread_sensitivity_years_signed` | expression / inherited | Complete reported investment-grade spread sensitivity, normalized to signed years. Cross-family conventions unverified. |
| `hy_spread_sensitivity_years_signed` | expression / inherited | Complete reported non-investment-grade spread sensitivity, normalized to signed years. |
| `risk_review` | expression / inherited |  |

## `risk_totals_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `accession_number` | TEXT | SEC filing accession number; amendments have separate accessions. |
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `risk_type` | TEXT | interest_rate or credit_spread. |
| `currency` | TEXT |  |
| `credit_bucket` | TEXT | Reported INVEST or NONINVEST credit spread bucket; not a position-level rating. |
| `shock_bp` | INTEGER | Shock size in basis points; 1 and 100 are retained separately. |
| `tenor_rows` | expression / inherited |  |
| `distinct_tenors` | expression / inherited |  |
| `nonmissing_tenors` | expression / inherited |  |
| `total_value_change_usd` | expression / inherited |  |
| `total_reported_sensitivity_years` | expression / inherited | Sum of five distinct complete normalized tenor observations; missing if incomplete. |

## `securities_lending_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `IS_CASH_COLLATERAL` | TEXT | Does any amount of this investment represent reinvestment of cash collateral received for loaned securities |
| `CASH_COLLATERAL_AMOUNT` | REAL | Provide the value of the investment representing cash collateral |
| `IS_NON_CASH_COLLATERAL` | TEXT | Does any portion of this investment represent non-cash collateral that is treated as a Fund asset and received for loaned securities |
| `NON_CASH_COLLATERAL_VALUE` | REAL | Provide the value of the securities representing non-cash collateral |
| `IS_LOAN_BY_FUND` | TEXT | Is any portion of this investment on loan by the Fund |
| `LOAN_VALUE` | REAL | Provide the value of the securities on loan |

## `submission_latest_raw` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `fund_series_id` | TEXT |  |
| `holdings_report_date` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `ACCESSION_NUMBER` | TEXT | The 20-character string formed from the 18-digit number assigned by the Commission to each EDGAR submission. |
| `FILING_DATE` | TEXT | Filing date |
| `FILE_NUM` | TEXT | File number |
| `SUB_TYPE` | TEXT | NPORT-P, NPORT-P/A, NT NPORT-P |
| `REPORT_ENDING_PERIOD` | TEXT | Date of fiscal year-end |
| `REPORT_DATE` | TEXT | Date as of which information is reported |
| `IS_LAST_FILING` | TEXT | Does the Fund anticipate that this will be its final filing on Form N-PORT |

## `swaption_option_warnt_deriv_latest` (view)

| Field | SQLite type | Meaning / SEC description |
|---|---|---|
| `series_id` | TEXT | SEC series identifier; the primary fund identity. |
| `report_date` | TEXT | Exact portfolio measurement date. |
| `ACCESSION_NUMBER` | TEXT |  |
| `source_archive_id` | TEXT | SHA-256 identifier of the source archive; pair with filing or holding IDs for joins. |
| `source_row` | INTEGER | Parsed source record number, for traceability to the original TSV. |
| `HOLDING_ID` | TEXT | Key for each holding in the schedule of portfolio investments |
| `PUT_OR_CALL` | TEXT | Type, selected from among the following (put, call). Respond call for warrants |
| `WRITTEN_OR_PURCHASED` | TEXT | Payoff profile, selected from among the following (written, purchased). Respond purchased for warrants |
| `SHARES_CNT` | REAL | Number of shares of underlying reference instrument per contract |
| `PRINCIPAL_AMOUNT` | REAL | Principal amount of underlying reference instrument per contract |
| `CURRENCY_CODE` | TEXT | Currency code |
| `EXERCISE_PRICE` | REAL | Exercise price or rate |
| `EXPIRATION_DATE` | TEXT | Expiration date. |
| `UNREALIZED_APPRECIATION` | REAL | Unrealized appreciation or depreciation. Depreciation shall be reported as a negative number |
