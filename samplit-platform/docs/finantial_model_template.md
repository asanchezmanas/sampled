# FINANCIAL MODEL TEMPLATE - SAMPLIT

## 📊 OVERVIEW

Este documento es la **guía** para construir tu modelo financiero en Excel/Google Sheets.

**Estructura:** 8 sheets principales
**Horizonte:** 3-5 años (mensual año 1, trimestral después)
**Update:** Mensual (actuals vs projections)

---

## 🗂️ SHEET STRUCTURE

### Sheet 1: ASSUMPTIONS (Inputs)

**Todas las variables clave en UN sitio.**

#### Revenue Assumptions:

```
PRICING
────────────────────────────────
Starter Plan (€/mes):           29
Pro Plan (€/mes):               99
Enterprise Plan (€/mes):        299

Mix (% de clientes):
  Starter:                      20%
  Pro:                          60%
  Enterprise:                   20%

ARPU weighted avg:              €92

GROWTH
────────────────────────────────
Monthly Growth Rate (M-o-M):
  Year 1:                       15%
  Year 2:                       10%
  Year 3:                       7%

New Customers/Month:
  Month 1:                      5
  Month 6:                      20
  Month 12:                     40

Trial → Paid Conversion:        20%
  Improving to:                 25% (Year 2)

RETENTION
────────────────────────────────
Monthly Churn Rate:
  Year 1:                       5%
  Year 2:                       3%
  Year 3:                       2%

Expansion Revenue (upgrades):
  % customers upgrading/year:   30%
  Average upgrade value:        €30/mes
```

---

#### Cost Assumptions:

```
COST OF GOODS SOLD (COGS)
────────────────────────────────
Hosting (AWS):                  €0.50 / customer / mes
Payment processing (Stripe):    2.9% + €0.30 / transaction
Support tools:                  €500 / mes (flat)

COGS as % revenue:              15%

SALES & MARKETING
────────────────────────────────
CAC (Customer Acquisition Cost): €120
  Breakdown:
    - Paid ads:                 €50
    - Content/SEO:              €20
    - Sales time:               €30
    - Tools:                    €20

CAC improving to:               €100 (Year 2)

Marketing Budget (% revenue):
  Year 1:                       30%
  Year 2:                       25%
  Year 3:                       20%

PERSONNEL
────────────────────────────────
Founder salary:                 €40k/year
CS Manager:                     €35k/year (starts Month 3)
Sales AE:                       €50k/year (starts Month 5)
Content Marketer:               €38k/year (starts Month 8)
Backend Dev:                    €50k/year (starts Month 10)

Employer costs (SS):            +30%

Annual raises:                  5%

OPERATIONS
────────────────────────────────
Software/Tools:                 €500/mes
Legal/Accounting:               €800/mes
Insurance:                      €200/mes
Office/Coworking:               €0 (remote)
Misc:                           €300/mes

Total Ops:                      €1,800/mes (€21,600/year)
```

---

### Sheet 2: REVENUE MODEL

**Monthly breakdown, Year 1:**

```
         Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec
──────────────────────────────────────────────────────────────────────
New Cust   5    6    7    8   10   12   14   17   20   23   27   32
Churned    0   -1   -1   -2   -2   -3   -3   -4   -5   -6   -7   -8
Total     5   10   16   22   30   39   50   63   78   95  115  139

MRR:
Starter   €150  €300  €500  €700  €950 €1,200 €1,550 €1,950
Pro      €500 €1,000 €1,650 €2,300 €3,150 €4,050 €5,150 €6,500
Enterprise €150 €300  €500  €700  €950 €1,200 €1,550 €1,950

Total MRR €800 €1,600 €2,650 €3,700 €5,050 €6,450 €8,250 €10,400

Growth%    -    100%   66%   40%   36%   28%   28%   26%
```

**Formulas en Excel:**
```
New Customers = PREVIOUS + (PREVIOUS × Growth Rate)
Churned = TOTAL × Churn Rate
Total Customers = PREVIOUS + New - Churned
MRR = Total Customers × (Starter% × €29 + Pro% × €99 + Enterprise% × €299)
```

---

### Sheet 3: CUSTOMER METRICS

**Cohort Analysis:**

```
Cohort     Month 0  Month 1  Month 2  Month 3  Month 6  Month 12
────────────────────────────────────────────────────────────────────
Jan '25      100      95       91       87       78       65
Feb '25      100      95       91       87       78       -
Mar '25      100      95       91       87       -        -

Retention =  100%     95%      91%      87%      78%      65%
Churn    =    0%      5%       4%       4%       3%       2%
```

**Key Metrics:**
```
LTV (Lifetime Value):
  Formula: ARPU / Churn Rate
  Year 1: €92 / 5% = €1,840
  Year 2: €95 / 3% = €3,167
  Year 3: €98 / 2% = €4,900

CAC Payback Period:
  Formula: CAC / (ARPU × Gross Margin)
  Year 1: €120 / (€92 × 85%) = 1.5 months

LTV/CAC Ratio:
  Year 1: €1,840 / €120 = 15.3x
  Year 2: €3,167 / €100 = 31.7x
  Year 3: €4,900 / €90 = 54.4x
```

---

### Sheet 4: PROFIT & LOSS (P&L)

**Monthly, Year 1:**

```
                    Jan     Feb     Mar     Apr     May     Jun
──────────────────────────────────────────────────────────────────
REVENUE
MRR                 800    1,600   2,650   3,700   5,050   6,450
Setup fees            0        0       0       0       0       0
──────────────────────────────────────────────────────────────────
Total Revenue       800    1,600   2,650   3,700   5,050   6,450

COGS
Hosting             100      200     330     460     630     800
Payment fees         30       60      99     138     189     241
Support tools       500      500     500     500     500     500
──────────────────────────────────────────────────────────────────
Total COGS          630      760   929    1,098   1,319   1,541

Gross Profit        170      840   1,721   2,602   3,731   4,909
Gross Margin %      21%      53%     65%     70%     74%     76%

OPERATING EXPENSES

Sales & Marketing:
Paid ads          1,000    1,200   1,500   1,800   2,200   2,600
Content/SEO         500      600     700     800     900   1,000
Sales salary          0        0   3,000   3,000   4,200   4,200
Tools/CRM           300      300     300     300     300     300
──────────────────────────────────────────────────────────────────
Total S&M         1,800    2,100   5,500   5,900   7,600   8,100

Personnel:
Founder          3,333    3,333   3,333   3,333   3,333   3,333
CS Manager           0        0   2,900   2,900   2,900   2,900
Sales AE             0        0       0       0   4,200   4,200
Backend Dev          0        0       0       0       0       0
Payroll tax (30%)  1,000    1,000   1,870   1,870   3,130   3,130
──────────────────────────────────────────────────────────────────
Total Personnel   4,333    4,333   8,103   8,103  13,563  13,563

Operations:
Software/tools      500      500     500     500     500     500
Legal/accounting    800      800     800     800     800     800
Insurance           200      200     200     200     200     200
Misc                300      300     300     300     300     300
──────────────────────────────────────────────────────────────────
Total Ops         1,800    1,800   1,800   1,800   1,800   1,800

──────────────────────────────────────────────────────────────────
Total OpEx        7,933    8,233  15,403  15,803  22,963  23,463

──────────────────────────────────────────────────────────────────
EBITDA           -7,763   -7,393 -13,682 -13,201 -19,232 -18,554

──────────────────────────────────────────────────────────────────
EBITDA Margin %  -970%    -462%   -516%   -357%   -381%   -288%

Burn Rate/Month   7,763    7,393  13,682  13,201  19,232  18,554
```

**Continue through Dec, then quarterly for Years 2-3.**

**Goal:** EBITDA positive by Month 18-24.

---

### Sheet 5: CASH FLOW

```
                    Jan      Feb      Mar      Apr      May
──────────────────────────────────────────────────────────────
OPERATING ACTIVITIES

Cash from customers   800    1,600    2,650    3,700    5,050
Cash to suppliers    -630     -760     -929   -1,098   -1,319
Cash to employees  -4,333   -4,333   -8,103   -8,103  -13,563
Cash to vendors    -3,600   -3,900   -7,300   -7,700  -10,200
──────────────────────────────────────────────────────────────
Net Operating CF   -7,763   -7,393  -13,682  -13,201  -19,232

INVESTING ACTIVITIES

Equipment purchase    -500        0   -1,000        0        0
Software development     0        0        0        0        0
──────────────────────────────────────────────────────────────
Net Investing CF      -500        0   -1,000        0        0

FINANCING ACTIVITIES

Funding raised     200,000        0        0        0        0
Loan repayment           0        0        0        0        0
──────────────────────────────────────────────────────────────
Net Financing CF   200,000        0        0        0        0

──────────────────────────────────────────────────────────────
NET CASH FLOW      191,737   -7,393  -14,682  -13,201  -19,232

Beginning Balance        0  191,737  184,344  169,662  156,461
Ending Balance     191,737  184,344  169,662  156,461  137,229

──────────────────────────────────────────────────────────────
Months of Runway        24       23       18       15       12
```

**Runway Formula:** 
`Ending Balance / Average Monthly Burn`

**Critical:** Track runway monthly. <6 months = fundraise NOW.

---

### Sheet 6: BALANCE SHEET

```
                               Jan        Feb        Mar
────────────────────────────────────────────────────────
ASSETS

Current Assets:
  Cash                      191,737    184,344    169,662
  Accounts Receivable             0          0          0
  Prepaid Expenses                0          0          0
────────────────────────────────────────────────────────
Total Current Assets        191,737    184,344    169,662

Fixed Assets:
  Equipment                     500        500      1,500
  Accumulated Depreciation        0        -10        -30
────────────────────────────────────────────────────────
Total Fixed Assets              500        490      1,470

────────────────────────────────────────────────────────
TOTAL ASSETS                192,237    184,834    171,132

────────────────────────────────────────────────────────
LIABILITIES

Current Liabilities:
  Accounts Payable                0        500      1,200
  Accrued Expenses                0        200        500
────────────────────────────────────────────────────────
Total Liabilities                 0        700      1,700

────────────────────────────────────────────────────────
EQUITY

Common Stock                200,000    200,000    200,000
Retained Earnings            -7,763    -15,866    -30,568
────────────────────────────────────────────────────────
Total Equity                192,237    184,134    169,432

────────────────────────────────────────────────────────
TOTAL LIABILITIES & EQUITY  192,237    184,834    171,132
```

**Check:** Assets = Liabilities + Equity (always!)

---

### Sheet 7: SCENARIOS

**Build 3 scenarios:**

#### Scenario A: BASE CASE (Most Likely)
- Assumptions as stated
- 15% M-o-M growth Year 1
- 20% trial→paid conversion
- 5% churn

---

#### Scenario B: BEST CASE (Optimistic)
- 20% M-o-M growth Year 1
- 30% trial→paid conversion
- 3% churn
- CAC €80 (better than expected)

**Outcomes:**
- €80k MRR by Month 12 (vs €50k base)
- Break-even Month 15 (vs Month 18)
- Need €150k funding (vs €200k)

---

#### Scenario C: WORST CASE (Conservative)
- 10% M-o-M growth Year 1
- 15% trial→paid conversion
- 7% churn
- CAC €150 (worse than expected)

**Outcomes:**
- €30k MRR by Month 12
- Break-even Month 24+
- Need €250k funding (burn faster)

**Use for:** Stress testing, fundraising prep

---

### Sheet 8: DASHBOARD (Summary)

**Key Metrics at-a-glance:**

```
╔════════════════════════════════════════════════════╗
║              SAMPLIT DASHBOARD                     ║
║              As of: [Current Month]                ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  REVENUE METRICS                                   ║
║  ─────────────────────────────────────────────    ║
║  MRR:                €X,XXX                        ║
║  ARR:                €XX,XXX                       ║
║  M-o-M Growth:       XX%                           ║
║  Total Customers:    XXX                           ║
║  ARPU:               €XX                           ║
║                                                    ║
║  CUSTOMER METRICS                                  ║
║  ─────────────────────────────────────────────    ║
║  New Customers:      XX (this month)               ║
║  Churned:            X                             ║
║  Churn Rate:         X%                            ║
║  Trial → Paid:       XX%                           ║
║  CAC:                €XXX                          ║
║  LTV:                €X,XXX                        ║
║  LTV/CAC:            XX.Xx                         ║
║  Payback Period:     X.X months                    ║
║                                                    ║
║  FINANCIAL HEALTH                                  ║
║  ─────────────────────────────────────────────    ║
║  Gross Margin:       XX%                           ║
║  EBITDA:             -€X,XXX (or +€X,XXX)          ║
║  Cash Balance:       €XX,XXX                       ║
║  Monthly Burn:       €X,XXX                        ║
║  Runway:             XX months                     ║
║                                                    ║
║  TEAM                                              ║
║  ─────────────────────────────────────────────    ║
║  Headcount:          X                             ║
║  Cost/Employee:      €X,XXX/mes                    ║
║                                                    ║
╚════════════════════════════════════════════════════╝
```

**Charts to Include:**
- MRR over time (line chart)
- Revenue breakdown by plan (stacked bar)
- Cash balance over time (line chart)
- Customer acquisition funnel (funnel chart)
- Cohort retention (heatmap)

---

## 📐 FORMULAS REFERENCE

### Key Calculations:

**MRR (Monthly Recurring Revenue):**
```
= SUM(Customers × Price per Plan)
```

**ARR (Annual Recurring Revenue):**
```
= MRR × 12
```

**Churn Rate:**
```
= Customers Lost / Total Customers at Start of Period
```

**CAC (Customer Acquisition Cost):**
```
= Total Sales & Marketing Spend / New Customers Acquired
```

**LTV (Lifetime Value):**
```
= ARPU / Churn Rate
OR
= ARPU × Gross Margin × (1 / Churn Rate)
```

**CAC Payback Period:**
```
= CAC / (ARPU × Gross Margin)
```

**LTV/CAC Ratio:**
```
= LTV / CAC
```
**Target: >3x (good), >5x (great)**

**Gross Margin:**
```
= (Revenue - COGS) / Revenue × 100%
```

**EBITDA:**
```
= Revenue - COGS - Operating Expenses
```

**Burn Rate:**
```
= -EBITDA (when negative)
```

**Runway:**
```
= Cash Balance / Monthly Burn Rate
```

---

## 🎯 BENCHMARKS (SaaS B2B)

### Good vs Great:

```
Metric                    Good      Great
──────────────────────────────────────────
Gross Margin              75%+      85%+
EBITDA Margin (mature)    20%+      30%+

CAC Payback               <12mo     <6mo
LTV/CAC                   3-5x      >5x
Churn (monthly)           <5%       <3%

Growth (early stage)      10%+      20%+
Growth (scale stage)      5%+       10%+

Trial → Paid              15-25%    25-35%
```

**Use these to benchmark your assumptions.**

---

## 📊 ACTUALS vs PROJECTIONS

### Monthly Tracking:

```
Metric           Projected   Actual   Variance   %Diff
─────────────────────────────────────────────────────
MRR              €5,000     €4,750    -€250     -5%
New Customers    10         9         -1        -10%
Churn            5%         6%        +1%       +20%
CAC              €120       €135      +€15      +13%
Burn             €15k       €16.5k    +€1.5k    +10%
```

**Review monthly. Adjust projections quarterly.**

**Questions:**
- Why the variance?
- Temporary or trend?
- What to adjust?

---

## 💡 MODEL BEST PRACTICES

### DO:

✅ **Keep it simple**
Start basic, add complexity as needed

✅ **Document assumptions**
Why this growth rate? Why this churn?

✅ **Version control**
Name files: "Samplit_Model_v2.3_[Date]"

✅ **Separate inputs from calculations**
Assumptions sheet = easy to adjust

✅ **Use consistent units**
All € (not mix of €/$/£)

✅ **Color code**
- Blue = inputs (you change)
- Black = formulas (auto-calculate)
- Red = negative (warnings)

✅ **Monthly Year 1, Quarterly after**
Too granular = noise

✅ **Update with actuals**
Model is living document

---

### DON'T:

❌ **Hard-code numbers in formulas**
Use cell references

❌ **Over-complicate**
100-row model > 1000-row model

❌ **Fantasy projections**
Be conservative (especially for investors)

❌ **Ignore actuals**
If reality diverges, update model

❌ **Forget to save**
Auto-save + backups

---

## 🚨 RED FLAGS IN YOUR MODEL

### Warning Signs:

❌ **Revenue grows but burn increases faster**
Not sustainable

❌ **CAC > LTV**
You lose money on every customer

❌ **Gross margin <50%**
Something's wrong (SaaS should be 75-90%)

❌ **Runway <6 months**
Fundraise NOW

❌ **Growth assumptions with no justification**
"We'll grow 50% M-o-M because we're awesome" ≠ plan

❌ **No scenario analysis**
What if things go wrong?

---

## 📧 SENDING TO INVESTORS

### What to Include:

**Email:**
```
Subject: Samplit - Financial Model

Hi [Name],

As requested, attached is our 3-year financial model.

Key highlights:
• €50k MRR by Month 12
• EBITDA positive Month 18
• LTV/CAC of 15x
• 18-month runway with €200k

Assumptions are conservative (explained in 
'Assumptions' sheet). Happy to walk through 
on a call.

Let me know if you have questions!

Best,
[Your Name]
```

**Attachment:**
- Excel file (not Google Sheets link for first send)
- PDF version (for easy viewing)
- 1-pager summary (if helpful)

---

### Investor Questions (Be Ready):

**"Why this growth rate?"**
*"Based on 3 similar SaaS companies in España at our stage (X, Y, Z) who averaged 12-18% M-o-M in year 1. We're assuming 15% (middle of range)."*

**"Why this churn rate?"**
*"Industry benchmark for B2B SaaS is 5-7%. We're assuming 5% to start, improving to 3% as we improve onboarding and product."*

**"When do you break even?"**
*"Month 18 in base case, Month 15 in best case. That's with €200k raised. If we raise more, we can invest in growth and break-even might be later but with higher revenue."*

**"What happens if revenue is 20% lower?"**
*"See 'Worst Case' scenario sheet. Break-even extends to Month 24, and we'd need €250k to cover burn. Still viable, just slower."*

---

## ✅ MODEL CHECKLIST

### Before Sharing:

- [ ] All formulas working (no #REF!, #DIV/0!)
- [ ] Assumptions clearly documented
- [ ] Numbers formatted consistently (€, comma separators)
- [ ] Charts/graphs clear and labeled
- [ ] 3 scenarios (base, best, worst)
- [ ] Actuals updated (if any)
- [ ] Balance sheet balances
- [ ] Cash flow ties to P&L
- [ ] Runway calculated correctly
- [ ] File named descriptively
- [ ] PDF version generated
- [ ] Spellcheck (especially if Spanish/English mix)

---

## 🎯 TEMPLATE DOWNLOAD

**Create in Google Sheets (recommended) or Excel.**

**Structure:**
```
Sheet 1: Assumptions (all inputs)
Sheet 2: Revenue Model (monthly detail)
Sheet 3: Customer Metrics (cohorts, LTV, CAC)
Sheet 4: P&L (income statement)
Sheet 5: Cash Flow
Sheet 6: Balance Sheet
Sheet 7: Scenarios (base/best/worst)
Sheet 8: Dashboard (visual summary)
```

**Protip:** Start simple. Add complexity only as needed.

**Most important:** 
- Track actuals vs projections monthly
- Adjust assumptions based on reality
- Use as tool for decision-making (not just fundraising)

---

## 💡 WHEN TO UPDATE MODEL

### Update Frequency:

**Monthly (Actuals):**
- Input actual revenue, costs, customers
- Compare to projections
- Adjust short-term forecast if needed

**Quarterly (Projections):**
- Review assumptions
- Adjust growth rates based on trends
- Update hiring plan
- Revise scenarios

**As Needed (Major Changes):**
- Fundraising (new capital)
- Pricing changes
- New product lines
- Major pivot

---

**Your financial model is your roadmap. Keep it updated, realistic, and use it to make decisions. 📊**
