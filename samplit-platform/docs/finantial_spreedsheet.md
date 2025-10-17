# FINANCIAL SPREADSHEET TEMPLATE - SAMPLIT

## 📊 GOOGLE SHEETS STRUCTURE

### Crear nuevo Google Sheet con estas pestañas:

```
Tab 1: 📊 DASHBOARD (resumen visual)
Tab 2: 💰 CASH FLOW (mes a mes)
Tab 3: 📈 P&L (Profit & Loss)
Tab 4: 🏦 BALANCE SHEET
Tab 5: 👥 CUSTOMERS (tracking clientes)
Tab 6: 💳 EXPENSES (gastos detallados)
Tab 7: 🎯 PROJECTIONS (12 meses)
Tab 8: 📋 ASSUMPTIONS (variables clave)
```

---

## TAB 1: 📊 DASHBOARD

### Layout:

```
╔═══════════════════════════════════════════════════════════╗
║                    SAMPLIT DASHBOARD                      ║
║                   Actualizado: [Fecha]                    ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  MÉTRICAS CLAVE                                          ║
║  ┌─────────────┬─────────────┬─────────────┬───────────┐║
║  │    MRR      │  Customers  │    Cash     │  Runway   │║
║  │  €[AUTO]    │   [AUTO]    │  €[AUTO]    │ [AUTO]mo  │║
║  │  +X% MoM    │   +Y% MoM   │  +Z% MoM    │           │║
║  └─────────────┴─────────────┴─────────────┴───────────┘║
║                                                           ║
║  ESTE MES                                                ║
║  ┌─────────────┬─────────────┬─────────────┬───────────┐║
║  │  Revenue    │  Expenses   │Cash Flow    │  Churn    │║
║  │  €[AUTO]    │  €[AUTO]    │ €[AUTO]     │  [AUTO]%  │║
║  └─────────────┴─────────────┴─────────────┴───────────┘║
║                                                           ║
║  GRÁFICO: MRR Growth (últimos 12 meses)                 ║
║  [Gráfico de línea auto-generado]                       ║
║                                                           ║
║  GRÁFICO: Cash Flow (últimos 6 meses)                   ║
║  [Gráfico de barras auto-generado]                      ║
║                                                           ║
║  ⚠️ ALERTS                                               ║
║  [Automático: Si runway <6 meses, muestra alerta]       ║
║  [Automático: Si churn >7%, muestra alerta]             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

### Fórmulas Dashboard:

**Cell B2 (MRR Actual):**
```
=SUMIF(Customers!D:D,"Active",Customers!E:E)
```
*Suma MRR de todos los clientes activos*

**Cell C2 (Total Customers):**
```
=COUNTIF(Customers!D:D,"Active")
```
*Cuenta clientes con status "Active"*

**Cell D2 (Cash en Banco):**
```
='Cash Flow'!L2
```
*Referencia al último mes del cash flow*

**Cell E2 (Runway en meses):**
```
=IF('Cash Flow'!M2<0, D2/'Cash Flow'!M2, "∞")
```
*Cash / Burn Rate mensual promedio*

**Cell B3 (MRR Growth % MoM):**
```
=(B2-'Cash Flow'!B11)/'Cash Flow'!B11
```
*Format: Percentage*

**Cell F3 (Churn Rate):**
```
=SUM('Cash Flow'!H2:H2)/B2
```
*Churned MRR / Total MRR*

---

## TAB 2: 💰 CASH FLOW

### Estructura:

```
┌─────┬──────┬────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
│  A  │  B   │   C    │    D    │    E    │    F    │    G    │    H    │
├─────┼──────┼────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│Month│ MRR  │New MRR │Churn MRR│Expansion│Cash In  │Cash Out │Net Cash │
├─────┼──────┼────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│Jan  │1,000 │  1,000 │    0    │    0    │  1,200  │  2,500  │  -1,300 │
│Feb  │1,200 │    250 │   50    │    0    │  1,450  │  2,600  │  -1,150 │
│Mar  │1,400 │    300 │   100   │    0    │  1,700  │  2,700  │  -1,000 │
│...  │      │        │         │         │         │         │         │
└─────┴──────┴────────┴─────────┴─────────┴─────────┴─────────┴─────────┘

┌─────┬─────────┬──────────┬───────────┐
│  I  │    J    │    K     │     L     │
├─────┼─────────┼──────────┼───────────┤
│Burn │Cash Beg │Cash End  │  Runway   │
│Rate │of Month │of Month  │  (months) │
├─────┼─────────┼──────────┼───────────┤
│1,300│  5,000  │  3,700   │    2.8    │
│1,150│  3,700  │  2,550   │    2.2    │
│1,000│  2,550  │  1,550   │    1.6    │
│     │         │          │           │
└─────┴─────────┴──────────┴───────────┘
```

### Fórmulas Cash Flow:

**B2 (MRR del mes):**
```
=B1+C2-D2+E2
```
*MRR anterior + Nuevo MRR - Churn + Expansion*

**C2 (New MRR):**
*Manual entry o referencia a Customers tab*

**D2 (Churn MRR):**
```
=SUMIF(Customers!G:G, A2, Customers!F:F)
```
*Suma MRR de clientes que churnaron este mes*

**F2 (Cash In):**
```
=SUMIFS(Customers!H:H, Customers!I:I, A2)
```
*Suma todos los pagos recibidos este mes*

**G2 (Cash Out):**
```
=SUMIFS(Expenses!C:C, Expenses!A:A, A2)
```
*Suma todos los gastos de este mes*

**H2 (Net Cash Flow):**
```
=F2-G2
```

**I2 (Burn Rate):**
```
=ABS(H2)
```
*Si es negativo*

**J2 (Cash Beginning):**
```
=K1
```
*Cash End del mes anterior*

**K2 (Cash End):**
```
=J2+H2
```

**L2 (Runway):**
```
=IF(I2<0, K2/ABS(I2), "∞")
```
*Si burn rate negativo, calcula meses restantes*

---

## TAB 3: 📈 P&L (PROFIT & LOSS)

### Estructura:

```
┌────────────────────────────────┬─────┬─────┬─────┬─────┬─────┐
│                                │ Jan │ Feb │ Mar │ Apr │ ... │
├────────────────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ REVENUE                        │     │     │     │     │     │
│   Subscription Revenue         │1,000│1,200│1,400│1,600│     │
│   Setup Fees                   │  100│   50│   50│    0│     │
│   Other Revenue                │    0│    0│    0│    0│     │
├────────────────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ TOTAL REVENUE                  │1,100│1,250│1,450│1,600│     │
├────────────────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ COST OF GOODS SOLD (COGS)      │     │     │     │     │     │
│   Hosting (AWS, etc)           │  200│  210│  220│  230│     │
│   Payment Processing (3%)      │   33│   38│   44│   48│     │
│   Customer Support Tools       │   50│   50│   50│   50│     │
├────────────────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ TOTAL COGS                     │  283│  298│  314│  328│     │
├────────────────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ GROSS PROFIT                   │  817│  952│1,136│1,272│     │
│ Gross Margin %                 │  74%│  76%│  78%│  80%│     │
├────────────────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ OPERATING EXPENSES             │     │     │     │     │     │
│   Salaries                     │2,000│2,000│2,000│2,500│     │
│   Marketing                    │  500│  600│  700│  800│     │
│   Software/Tools               │  200│  200│  200│  200│     │
│   Legal/Accounting             │  150│  150│  150│  150│     │
│   Office/Other                 │  100│  100│  100│  100│     │
├────────────────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ TOTAL OPEX                     │2,950│3,050│3,150│3,750│     │
├────────────────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ EBITDA                         │-2,133│-2,098│-2,014│-2,478│     │
│ EBITDA Margin %                │-194%│-168%│-139%│-155%│     │
├────────────────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ Depreciation & Amortization    │   50│   50│   50│   50│     │
│ Interest Expense (if debt)     │    0│    0│    0│    0│     │
├────────────────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ NET INCOME (Profit/Loss)       │-2,183│-2,148│-2,064│-2,528│     │
│ Net Margin %                   │-198%│-172%│-142%│-158%│     │
└────────────────────────────────┴─────┴─────┴─────┴─────┴─────┘
```

### Fórmulas P&L:

**B4 (Subscription Revenue):**
```
='Cash Flow'!B2
```
*Referencia al MRR del mes (esto es simplificado)*

**Para revenue recognition correcto (con anuales):**
```
=SUMIFS(Customers!E:E, Customers!D:D, "Active") 
+ (SUMIFS(Customers!J:J, Customers!K:K, "Annual", Customers!L:L, "<=B1")/12)
```
*MRR de mensuales + (Pagos anuales / 12)*

**B6 (Payment Processing 3%):**
```
=B4*0.03
```

**B10 (Gross Profit):**
```
=B4-B8
```

**B11 (Gross Margin %):**
```
=B10/B4
```
*Format: Percentage*

**B21 (EBITDA):**
```
=B10-B19
```

**B26 (Net Income):**
```
=B21-B23-B24
```

---

## TAB 4: 🏦 BALANCE SHEET

### Estructura:

```
┌────────────────────────────────┬─────────┬─────────┬─────────┐
│          ASSETS                │  Jan 31 │  Feb 28 │  Mar 31 │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ CURRENT ASSETS                 │         │         │         │
│   Cash                         │  3,700  │  2,550  │  1,550  │
│   Accounts Receivable          │    200  │    150  │    180  │
│   Prepaid Expenses             │    500  │    450  │    400  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ TOTAL CURRENT ASSETS           │  4,400  │  3,150  │  2,130  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ FIXED ASSETS                   │         │         │         │
│   Equipment (computer, etc)    │  2,000  │  2,000  │  2,000  │
│   Accumulated Depreciation     │   -100  │   -150  │   -200  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ TOTAL FIXED ASSETS             │  1,900  │  1,850  │  1,800  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ TOTAL ASSETS                   │  6,300  │  5,000  │  3,930  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│                                │         │         │         │
│          LIABILITIES           │         │         │         │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ CURRENT LIABILITIES            │         │         │         │
│   Accounts Payable             │    300  │    250  │    200  │
│   Deferred Revenue (Annual)    │  8,000  │  7,500  │  7,000  │
│   Current Portion Debt         │    500  │    500  │    500  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ TOTAL CURRENT LIABILITIES      │  8,800  │  8,250  │  7,700  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ LONG-TERM LIABILITIES          │         │         │         │
│   Long-term Debt               │  5,000  │  4,500  │  4,000  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ TOTAL LIABILITIES              │ 13,800  │ 12,750  │ 11,700  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│                                │         │         │         │
│          EQUITY                │         │         │         │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│   Paid-in Capital              │ 10,000  │ 10,000  │ 10,000  │
│   Retained Earnings (Losses)   │-17,500  │-17,750  │-17,770  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ TOTAL EQUITY                   │ -7,500  │ -7,750  │ -7,770  │
├────────────────────────────────┼─────────┼─────────┼─────────┤
│ TOTAL LIAB + EQUITY            │  6,300  │  5,000  │  3,930  │
└────────────────────────────────┴─────────┴─────────┴─────────┘
```

### Fórmulas Balance:

**B2 (Cash):**
```
='Cash Flow'!K2
```

**B5 (Deferred Revenue):**
```
=SUMIFS(Customers!M:M, Customers!D:D, "Active", Customers!K:K, "Annual")
```
*Suma balance de planes anuales no reconocidos*

**B13 (Total Assets):**
```
=B9+B12
```

**B24 (Total Liabilities):**
```
=B18+B21
```

**B27 (Retained Earnings):**
```
=B26+'P&L'!B26
```
*Earnings anteriores + Net Income de este mes*

**B29 (Total Equity):**
```
=B26+B27
```

**Check (Total Assets = Liab + Equity):**
```
=IF(B13=B31, "✓ Balanced", "⚠ ERROR")
```

---

## TAB 5: 👥 CUSTOMERS

### Estructura:

```
┌───┬──────────┬──────────┬────────┬─────┬──────┬───────┬────────┬────────────┐
│ A │    B     │    C     │   D    │  E  │  F   │   G   │   H    │     I      │
├───┼──────────┼──────────┼────────┼─────┼──────┼───────┼────────┼────────────┤
│ID │   Name   │  Email   │ Status │ MRR │Churn │Churn  │Payment │Payment Date│
│   │          │          │        │     │ MRR  │ Date  │Received│            │
├───┼──────────┼──────────┼────────┼─────┼──────┼───────┼────────┼────────────┤
│001│Company A │a@co.com  │Active  │  29 │      │       │   29   │  2025-01-15│
│002│Company B │b@co.com  │Active  │  99 │      │       │  348   │  2025-01-10│
│003│Company C │c@co.com  │Churned │     │  29  │2025-02│   29   │  2025-01-20│
│004│Company D │d@co.com  │Active  │  29 │      │       │   29   │  2025-02-01│
│...│          │          │        │     │      │       │        │            │
└───┴──────────┴──────────┴────────┴─────┴──────┴───────┴────────┴────────────┘

┌───┬────────┬────────┬───────────┬─────────┐
│ J │   K    │   L    │     M     │    N    │
├───┼────────┼────────┼───────────┼─────────┤
│Pmt│  Plan  │ Start  │ Deferred  │  Notes  │
│Amt│  Type  │  Date  │  Revenue  │         │
├───┼────────┼────────┼───────────┼─────────┤
│ 29│Monthly │2025-01 │     0     │         │
│348│Annual  │2025-01 │   319     │Early    │
│ 29│Monthly │2025-01 │     0     │Churned  │
│ 29│Monthly │2025-02 │     0     │         │
│   │        │        │           │         │
└───┴────────┴────────┴───────────┴─────────┘
```

### Fórmulas Customers:

**E2 (MRR):**
```
=IF(D2="Active", IF(K2="Monthly", J2, J2/12), 0)
```
*Si activo: si mensual = pago full, si anual = pago/12*

**F2 (Churn MRR):**
*Manual cuando cliente cancela*

**M2 (Deferred Revenue):**
```
=IF(AND(K2="Annual", D2="Active"), 
   J2 - (J2/12)*DATEDIF(L2, TODAY(), "M"), 
   0)
```
*Para anuales: Total pago - (meses transcurridos × MRR mensual)*

---

## TAB 6: 💳 EXPENSES

### Estructura:

```
┌──────────┬─────────────┬────────┬─────────────┬──────────┬────────┐
│    A     │      B      │   C    │      D      │    E     │   F    │
├──────────┼─────────────┼────────┼─────────────┼──────────┼────────┤
│   Date   │  Category   │ Amount │ Description │  Vendor  │Receipt │
├──────────┼─────────────┼────────┼─────────────┼──────────┼────────┤
│2025-01-05│   Hosting   │  150   │AWS usage    │   AWS    │ Y      │
│2025-01-10│   Software  │   50   │Analytics    │ Mixpanel │ Y      │
│2025-01-15│  Marketing  │  200   │LinkedIn ads │ LinkedIn │ Y      │
│2025-01-20│   Salary    │ 2,000  │Founder sal. │   Self   │ N      │
│2025-01-25│   Legal     │  150   │Accountant   │ Contador │ Y      │
│...       │             │        │             │          │        │
└──────────┴─────────────┴────────┴─────────────┴──────────┴────────┘
```

**Categorías estándar:**
- Hosting
- Software
- Marketing
- Salary
- Legal/Accounting
- Office
- Equipment
- Other

---

## TAB 7: 🎯 PROJECTIONS

### Estructura (12 meses futuros):

```
┌──────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│      │ M1  │ M2  │ M3  │ M4  │ M5  │ M6  │ ... │
├──────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ MRR  │1,600│1,900│2,250│2,650│3,100│3,600│     │
│Growth│ 100 │ 300 │ 350 │ 400 │ 450 │ 500 │     │
│Churn │  50 │  60 │  70 │  80 │  90 │ 100 │     │
├──────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│Rev   │1,600│1,900│2,250│2,650│3,100│3,600│     │
│COGS  │  350│  400│  470│  550│  640│  740│     │
│OpEx  │3,200│3,300│3,400│3,500│3,600│3,700│     │
├──────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│P/L   │-1,950│-1,800│-1,620│-1,400│-1,140│-840│     │
├──────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│Cash  │1,550│  800│  200│    0│  TBD│     │     │
└──────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
```

**Fórmulas basadas en assumptions (Tab 8):**

**B2 (MRR projected):**
```
='Cash Flow'!B[last] * (1 + Assumptions!$B$2)
```
*MRR actual × (1 + growth rate mensual)*

---

## TAB 8: 📋 ASSUMPTIONS

### Variables clave:

```
┌───────────────────────────────┬─────────┬────────┐
│         Variable              │  Value  │ Notes  │
├───────────────────────────────┼─────────┼────────┤
│ GROWTH                        │         │        │
│   MRR Growth Rate (monthly)   │   15%   │ Target │
│   New Customers/month         │    10   │ Goal   │
│   Avg MRR per customer        │   €50   │ Avg    │
├───────────────────────────────┼─────────┼────────┤
│ CHURN                         │         │        │
│   Churn Rate (monthly)        │    5%   │ Target │
│   Churn MRR/month             │   €80   │ Avg    │
├───────────────────────────────┼─────────┼────────┤
│ COSTS                         │         │        │
│   COGS as % Revenue           │   22%   │ Actual │
│   OpEx Growth (monthly)       │    3%   │ Plan   │
│   Marketing as % Revenue      │   30%   │ Target │
├───────────────────────────────┼─────────┼────────┤
│ CASH                          │         │        │
│   Starting Cash               │ €5,000  │ Actual │
│   Min Cash Buffer             │ €2,000  │ Safety │
│   Runway Target (months)      │    12   │ Goal   │
├───────────────────────────────┼─────────┼────────┤
│ CONVERSION                    │         │        │
│   Trial to Paid %             │   20%   │ Target │
│   CAC (Customer Acq Cost)     │  €100   │ Avg    │
│   LTV (Lifetime Value)        │  €500   │ Est    │
│   LTV/CAC Ratio               │   5.0   │ Good   │
└───────────────────────────────┴─────────┴────────┘
```

---

## 🎨 CONDITIONAL FORMATTING

### Dashboard Alerts:

**Runway Cell (Dashboard!E2):**
```
Si <3 meses: Rojo
Si 3-6 meses: Naranja
Si >6 meses: Verde
```

**Churn Cell (Dashboard!F3):**
```
Si >7%: Rojo
Si 5-7%: Naranja
Si <5%: Verde
```

**Cash Flow (Tab Cash Flow, columna H):**
```
Si negativo: Rojo
Si positivo: Verde
```

---

## 📊 GRÁFICOS AUTOMÁTICOS

### Dashboard:

**1. MRR Growth Chart**
- Tipo: Línea
- Data: Cash Flow!B:B (MRR por mes)
- X-axis: Meses
- Y-axis: MRR (€)

**2. Cash Flow Chart**
- Tipo: Barras
- Data: Cash Flow!H:H (Net Cash Flow)
- Colores: Rojo (negativo), Verde (positivo)

**3. P&L Summary**
- Tipo: Stacked Bar
- Data: Revenue, COGS, OpEx por mes
- Muestra: Gross Profit y Net Income

---

## 🔐 DATA VALIDATION

### Customers Tab:

**Column D (Status):**
```
Dropdown: Active, Churned, Trial, Paused
```

**Column K (Plan Type):**
```
Dropdown: Monthly, Annual
```

### Expenses Tab:

**Column B (Category):**
```
Dropdown: Hosting, Software, Marketing, Salary, 
          Legal, Office, Equipment, Other
```

---

## 📱 MOBILE VIEW

### Para revisar en móvil:

**Congela filas/columnas:**
- Dashboard: Freeze Row 1 y Column A
- Cash Flow: Freeze Row 1 y Column A
- P&L: Freeze Rows 1-2 y Column A

**Reduce zoom a 75%** para ver más info en pantalla pequeña.

---

## 🔄 ACTUALIZACIÓN MENSUAL

### Checklist (Primer día del mes):

1. **Tab Cash Flow:**
   - [ ] Añadir nueva fila con mes nuevo
   - [ ] Actualizar New MRR (de Customers)
   - [ ] Actualizar Churn MRR (de Customers)
   - [ ] Verificar Cash In (de Customers)
   - [ ] Actualizar Cash Out (de Expenses)

2. **Tab P&L:**
   - [ ] Añadir nueva columna con mes nuevo
   - [ ] Verificar Revenue recognition
   - [ ] Actualizar COGS
   - [ ] Actualizar OpEx

3. **Tab Balance Sheet:**
   - [ ] Añadir nueva columna con mes nuevo
   - [ ] Actualizar Cash (de Cash Flow)
   - [ ] Actualizar Deferred Revenue
   - [ ] Actualizar Retained Earnings

4. **Tab Customers:**
   - [ ] Marcar clientes churned
   - [ ] Añadir nuevos clientes
   - [ ] Actualizar pagos recibidos

5. **Tab Expenses:**
   - [ ] Añadir gastos del mes
   - [ ] Categorizar correctamente
   - [ ] Adjuntar receipts (links)

6. **Tab Projections:**
   - [ ] Revisar assumptions
   - [ ] Ajustar proyecciones
   - [ ] Update based on actuals

7. **Dashboard:**
   - [ ] Verificar todos los cálculos auto-updating
   - [ ] Revisar alerts
   - [ ] Screenshot para records

---

## 💾 BACKUP & VERSIONING

### Sistema de Versiones:

**Naming:**
```
Samplit_Financials_2025_v1.0
Samplit_Financials_2025_v1.1 (después de update mensual)
Samplit_Financials_2025_v2.0 (después de Q)
```

**Backup:**
- Download como Excel cada mes
- Guarda en Google Drive folder: /Financials/Backups/
- Keep last 12 meses

---

## 🎯 KPIs A MONITOREAR

### Diario:
- Cash in bank

### Semanal:
- New MRR this week
- Churn this week
- Runway

### Mensual:
- Total MRR
- MRR Growth %
- Churn Rate %
- Net Cash Flow
- Burn Rate
- Customer Count
- CAC
- LTV

### Trimestral:
- P&L Review
- Balance Sheet Health
- Projection vs Actual
- Adjust Assumptions

---

## ⚠️ ERRORES COMUNES A EVITAR

### ❌ NO HAGAS:

**1. Mezclar Cash con Revenue**
```
❌ Payment anual €1,200 ≠ €1,200 revenue mes 1
✅ Revenue = €100/mes × 12
```

**2. Olvidar Deferred Revenue**
```
❌ No trackear balance de anuales
✅ Trackear y reducir mensualmente
```

**3. Ignorar Small Expenses**
```
❌ "Son solo €20, no importa"
✅ Todo se suma. Track EVERYTHING
```

**4. No Actualizar Regularmente**
```
❌ Actualizar cada 3 meses
✅ Update mensual MÍNIMO
```

**5. Fórmulas Rotas**
```
❌ Copy/paste y romper referencias
✅ Verificar fórmulas después de cambios
```

---

## 📈 TEMPLATE LISTO PARA USAR

### Para implementar YA:

**Option 1: Crear desde cero**
- Copia la estructura arriba
- Implementa fórmulas
- Configura gráficos

**Option 2: Template pre-hecho**
- Busca: "SaaS Financial Model Template" Google Sheets
- Adapta a tu caso
- Asegúrate entiende todas las fórmulas

**Option 3: Hybrid**
- Empieza simple (Cash Flow + Dashboard)
- Añade tabs según necesites
- Crece con tu negocio

---

## 🎓 APRENDE A USARLO

### Primer Mes:

**Semana 1:**
- Setup estructura básica
- Input datos existentes
- Verificar fórmulas funcionan

**Semana 2-4:**
- Update diario/semanal
- Acostúmbrate al flujo
- Identifica qué falta

**Mes 2:**
- Añadir más detalle
- Custom views para ti
- Automatizar más

**Mes 3+:**
- Rutina establecida
- Proyecciones más precisas
- Decisiones data-driven

---

## 💡 TIPS AVANZADOS

### 1. Scenario Planning

Crea copias del Tab Projections:
- Best Case (growth 20%/mes)
- Base Case (growth 10%/mes)
- Worst Case (growth 5%/mes)

Ayuda a prepararte para diferentes outcomes.

---

### 2. Cohort Analysis

Añadir tab para tracking por cohort:
- Clientes Jan 2025
- Clientes Feb 2025
- etc.

Track retention/churn por cohort.

---

### 3. CAC Payback Period

Calcular cuántos meses tardas en recuperar CAC:
```
CAC Payback = CAC / (MRR × Gross Margin)
```

Target: <12 meses

---

### 4. Rule of 40

Métrica SaaS importante:
```
Rule of 40 = Growth Rate % + Profit Margin %

Target: ≥40%
```

---

## ✅ CHECKLIST IMPLEMENTACIÓN

- [ ] Crear Google Sheet nuevo
- [ ] Setup 8 tabs básicas
- [ ] Implementar fórmulas Dashboard
- [ ] Implementar fórmulas Cash Flow
- [ ] Setup tab Customers
- [ ] Setup tab Expenses
- [ ] Input datos históricos (si existen)
- [ ] Verificar todos los cálculos
- [ ] Configurar gráficos
- [ ] Configurar conditional formatting
- [ ] Hacer backup
- [ ] Compartir con contador
- [ ] Set reminder mensual para update

---

**Este spreadsheet es tu COCKPIT financiero.**

**Úsalo RELIGIOSAMENTE.**

**Tus decisiones serán 10x mejores con data clara.**
