# Exploratory Data Analysis Report: Online Retail II

**Candidate:** Igor Ganapolsky  
**Role:** Senior Forward Deployed Data & AI Engineer (candidate)  
**Dataset:** Online Retail II (UK Giftware Retailer, Dec 2009 – Dec 2011)  
**Deliverables:**
- Jupyter Notebook: `online_retail_ii_eda.ipynb`
- HTML Presentation: `online_retail_ii_eda.html`
- High-Resolution Charts: `figures/`

---

## 1. Executive Summary

This exploratory data analysis investigates **1,067,371 transaction records** spanning December 1, 2009 through December 9, 2011 from a UK-based online giftware retailer.

### Key Business Insights:
1. **Extreme Customer Revenue Concentration (B2B Wholesale Core):**
   - The **top 10% of customers account for 63.1% of total tracked revenue** (£10.56M), and the top 20% generate **76.6%**. The business is fundamentally a B2B wholesale distributor operating over an ecommerce interface.
2. **High-Margin International Expansion Corridors:**
   - While the domestic UK market accounts for **84.9%** of net revenue (£16.38M), international orders carry nearly **2x higher Average Order Value (£642.63 vs. £333.60)**. Key export hubs—the Netherlands (£2,194 AOV), Australia (£1,428 AOV), Denmark (£1,240 AOV), and EIRE (£764 AOV)—represent commercial bulk accounts.
3. **Pronounced Q4 Seasonal Whiplash:**
   - Sales exhibit severe seasonality: **October and November represent ~35% of annual volume** (peaking at ~£1.46M/mo), driven by holiday stocking, followed by elevated return and refund volumes in December and January.
4. **Data Hygiene & Identity Gap (22.8% Unregistered Checkouts):**
   - **243,007 transaction records (22.8%) lack a `Customer ID`**. Dropping these un-attributed guest checkouts would erase over £2.9M in gross sales. They must be preserved for inventory and revenue reporting but segmented out for customer cohort modeling.

---

## 2. Data Overview & Grain Analysis

### Dataset Semantics:
- **Grain:** Transaction line-item level (one line per distinct product within a customer invoice).
- **Time Horizon:** 24 months (2009-12-01 to 2011-12-09).
- **Core Entities:** Invoices (53,628 distinct), Products (5,305 distinct StockCodes), Customers (5,942 distinct accounts), Countries (43 geographic markets).
- **Total Gross Merchandise Value (GMV):** **£19.29M** across both years.

---

## 3. Data Quality Checks & Anomaly Auditing

| Anomaly Type | Record Count | % of Dataset | Business Impact & Engineering Treatment |
| :--- | :---: | :---: | :--- |
| **Missing `Customer ID`** | 243,007 | 22.77% | Represents guest checkouts or marketplace sales. Must be retained for product/revenue totals, but segmented out for cohort retention analyses. |
| **Cancellations (`Invoice` starting with 'C')** | 19,494 | 1.83% | Explicit returns/cancellations with negative quantities. Reduces net revenue by ~£1.3M. |
| **Non-Product Fee Codes** | 5,327 | 0.50% | `POST`, `DOT` (postage), `M` (manual adjustments), `BANK CHARGES`, `AMAZONFEE`. Filtered out of physical product demand forecasting. |
| **Zero-Price Records** | 6,202 | 0.58% | Promotional free gifts, sample distributions, or inventory write-offs. |
| **Missing Descriptions** | 4,382 | 0.41% | Unmapped items; resolved by joining across historical `StockCode` mappings. |

---

## 4. Exploratory Analysis & Statistical Breakdown

### A. Monthly Revenue & Seasonality
- **Peak Months:** November 2010 (£1.42M net) and November 2011 (£1.46M net).
- **Trough Months:** February 2010 (£533k) and February 2011 (£498k).
- **Post-Holiday Return Spikes:** January return rates spike to 4.8% of gross sales following holiday delivery cycles.

### B. Customer Pareto Concentration
- **Decile 1 (Top 10% Spenders, 585 accounts):** £10.56M (63.06% of total revenue).
- **Decile 2:** £2.27M (13.58% of revenue).
- **Decile 3–10 (Bottom 80%):** Combined £3.92M (23.36% of revenue).

### C. Geographic Market Performance
- **United Kingdom:** 49,108 invoices, 5,410 customers, **£16.38M net revenue** (84.94% share, £333.60 AOV).
- **International:** 4,520 invoices, 533 customers, **£2.90M net revenue** (15.06% share, £642.63 AOV).
  - *Netherlands:* £548,525 net revenue, **£2,194.10 AOV**.
  - *Australia:* £167,129 net revenue, **£1,428.45 AOV**.
  - *Denmark:* £65,741 net revenue, **£1,240.40 AOV**.
  - *EIRE:* £615,520 net revenue, **£763.67 AOV**.

### D. Top Revenue Products
1. `22423` — **REGENCY CAKESTAND 3 TIER**: 27,232 units sold, **£344,563.25** net revenue.
2. `85123A` — **WHITE HANGING HEART T-LIGHT HOLDER**: 99,704 units sold, **£263,109.67** net revenue.
3. `85099B` — **JUMBO BAG RED RETROSPOT**: 96,956 units sold, **£183,454.83** net revenue.
4. `23843` — **PAPER CRAFT , LITTLE BIRDIE**: 80,995 units sold, **£168,469.60** net revenue.
5. `47566` — **PARTY BUNTING**: 27,576 units sold, **£149,187.05** net revenue.

---

## 5. Structured Findings & Business Hypotheses

| # | Hypothesis / Finding | Strategic Business Impact | Confidence Level | Validation Approach |
|---|---|---|---|---|
| **H1** | **B2B Wholesale vs. B2C Retail Bifurcation:** The top 10% of customers represent repeat commercial re-sellers, generating 63.1% of revenue. | High: Tailoring bulk pricing tiers, dedicated account reps, and credit terms will protect high-margin revenue. | **High (95%)** | Confirmed via Pareto decile analysis and basket size distribution. |
| **H2** | **Q4 Holiday Inventory Whiplash:** Oct–Nov accounts for 35% of annual volume, followed by major post-holiday return spikes in Dec/Jan. | High: Stockouts in Q4 cause massive lost revenue, while over-ordering leads to post-holiday inventory write-downs. | **High (90%)** | Verified across 2 consecutive annual cycles (2010 and 2011). |
| **H3** | **International Corridors are High-Value Wholesale Hubs:** Non-UK European orders carry ~2x higher AOV (£642 vs £333), led by Netherlands (£2,194 AOV). | Medium-High: Expanding European B2B distributor partnerships is the most capital-efficient growth lever. | **High (85%)** | Backed by country-level AOV and order frequency metrics. |
| **H4** | **Guest Checkout Identity Blindspot (22.8% Unregistered):** 243k rows lack customer identifiers, distorting churn and LTV calculations. | Medium: Implementing post-checkout identity resolution (shipping address / payment tokens) recovers true cohort visibility. | **Medium (75%)** | Observed null customer IDs coinciding with bulk non-standard transactions. |

---

## 6. Caveats & Methodological Limitations

1. **Absence of Unit Costs & Margin Data:**
   - Dataset provides unit price (revenue) only. No Cost of Goods Sold (COGS), fulfillment, or return shipping costs are available.
2. **Missing Customer Identity on 22.8% of Rows:**
   - Customer retention, repeat purchase rates, and churn metrics only reflect logged-in/registered buyers.
3. **Right-Censored Time Horizon:**
   - The dataset terminates on December 9, 2011. December 2011 totals appear artificially low due to the incomplete month.

---

## 7. Recommended Next Steps (Client Engagement Roadmap)

1. **Phase 1: Production Data Engineering (Medallion Lakehouse)**
   - Ingest transaction drops into Bronze Delta tables using Databricks Auto Loader.
   - Conformed Silver models separating commercial wholesale orders from retail consumer checkouts.
   - Implement Great Expectations data quality gates to quarantine unmapped product codes and invalid prices.
2. **Phase 2: Customer Identity Resolution & RFM Segmentation**
   - Resolve guest transactions using tokenized billing addresses.
   - Build automated RFM (Recency, Frequency, Monetary) segmentation in dbt/Gold layer to trigger automated marketing workflows for VIP wholesale accounts.
3. **Phase 3: Predictive Inventory Demand & Churn Prevention**
   - Train hierarchical demand forecasting models (LightGBM/Prophet) to forecast product-level inventory requirements ahead of the Q4 holiday surge.
   - Deploy early-warning churn detection for top-decile B2B accounts.

---

## 8. Use of GenAI Disclosure

In accordance with exercise instructions, GenAI tools were utilized as an engineering assistant throughout the analysis:
- **Where GenAI was used:**
  - Generating initial DuckDB analytical SQL queries and standard Matplotlib visualization scaffolding.
  - Structuring the presentation framework and formatting the business hypothesis matrix.
- **What was challenged & modified:**
  - *Corrected Date Serialization:* Standard Excel date floats were initially misparsed by generic scripts; wrote custom epoch conversion for exact timestamp fidelity.
  - *Refined Cancellation Handling:* Caught that dropping 'C' prefix rows without tracking return dollar impacts distorted net sales.
  - *Catalog Fee Codes Filtered:* Explicitly isolated manual adjustment codes (`POST`, `DOT`, `M`) from true physical product volume.
- **Validation Methodology:**
  - All aggregation metrics and percentages were independently validated against raw DuckDB SQL computations and verified against underlying Parquet tables.
