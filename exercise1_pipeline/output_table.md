# Daily Sales Reporting Table (Gold Mart)

**Business Question Addressed:**  
Daily breakdown by product category and sales region providing:
1. **Net Revenue** (`SUM(quantity * unit_price)`)
2. **Order Count** (`COUNT(DISTINCT order_id)`)
3. **Units Sold** (`net_units_sold` / `gross_units_sold`)
4. **Average Order Value (AOV)** (`net_revenue / order_count`)

---

## 📊 Analytics Output Table

| Order Date | Category | Region | Net Revenue | Order Count | Net Units | Gross Units | AOV |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **2024-01-01** | Accessories | South | **$49.95** | 1 | 1 | 1 | $49.95 |
| **2024-01-01** | Electronics | East | **$74.97** | 2 | 3 | 3 | $37.48 |
| **2024-01-01** | Electronics | West | **$2,287.90** | 3 | 12 | 12 | $762.63 |
| **2024-01-01** | Home & Office | West | **$29.99** | 1 | 1 | 1 | $29.99 |
| **2024-01-01** | Kitchen | East | **$36.00** | 1 | 3 | 3 | $36.00 |
| **2024-01-01** | Kitchen | South | **$30.00** | 1 | 4 | 4 | $30.00 |
| **2024-01-01** | Stationery | North | **$21.00** | 2 | 6 | 6 | $10.50 |
| **2024-01-01** | Unknown | East | **$30.00** | 1 | 2 | 2 | $30.00 |
| **2024-01-02** | Accessories | West | **$49.95** | 1 | 1 | 1 | $49.95 |
| **2024-01-02** | Electronics | East | **$74.97** | 1 | 3 | 3 | $74.97 |
| **2024-01-02** | Electronics | North | **$44.95** | 1 | 5 | 5 | $44.95 |
| **2024-01-02** | Electronics | West | **-$1,099.00** | 1 | -1 | 0 | -$1,099.00 |
| **2024-01-02** | Home & Office | Unknown | **$59.98** | 1 | 2 | 2 | $59.98 |
| **2024-01-02** | Kitchen | South | **$24.00** | 1 | 2 | 2 | $24.00 |
| **2024-01-02** | Kitchen | West | **$22.50** | 1 | 3 | 3 | $22.50 |
| **2024-01-02** | Stationery | East | **$46.96** | 2 | 6 | 6 | $23.48 |
| **2024-01-02** | Unknown | South | **$19.99** | 1 | 1 | 1 | $19.99 |

---

### 🔍 Key Metrics Summary:
- **Total Unique Orders Processed Across Both Days:** 22 distinct orders (12 on Day 1, 10 net active on Day 2).
- **Day 1 Total Net Revenue:** **$2,559.81** (8 category-region groups)
- **Day 2 Total Net Revenue:** **-$760.70** (9 category-region groups, impacted by $1,099 return `O2004`)
- **Aggregate Conformed Net Revenue:** **$1,799.11** across all dates.
