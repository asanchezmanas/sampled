# FINANCIAL MANAGEMENT - SAMPLIT

## ⚠️ DISCLAIMER IMPORTANTE

**NO soy contador ni asesor financiero.** Esta guía es educativa.

**DEBES contratar:**
- ✅ Contador (desde día 1)
- ✅ Asesor fiscal (para impuestos)
- ✅ Revisar contabilidad mensualmente

**Esta guía te ayuda a entender, pero NO reemplaza profesionales.**

---

## 💰 LA CONFUSIÓN MORTAL: MRR ≠ CASH ≠ REVENUE

### El Problema:

**Muchos founders piensan:**
```
"Tengo €10,000 MRR = Tengo €10,000 en el banco"
❌ FALSO y PELIGROSO
```

**La realidad:**
```
MRR (Monthly Recurring Revenue) = Ingresos recurrentes mensuales
Cash (Efectivo) = Dinero REAL en el banco
Revenue (Ingresos) = Lo que puedes reconocer contablemente
```

**Son 3 cosas DIFERENTES.**

---

### Ejemplo Real:

**Escenario:** Vendes 1 plan anual de €1,200.

**Lo que pasa:**

```
DÍA 1 (Cliente paga):
┌─────────────────────────────────────┐
│ CASH (Banco):        +€1,200       │ ✅ Tienes el dinero
│ MRR:                 +€100          │ ✅ €1,200 / 12 meses
│ REVENUE (Mes 1):     +€100          │ ✅ Solo reconoces 1 mes
└─────────────────────────────────────┘

RESULTADO:
• Banco: €1,200 (puedes verlo)
• Contabilidad: €100 revenue
• MRR: €100

Los otros €1,100 son "Deferred Revenue" (ingresos diferidos)
= Debes el servicio por 11 meses más
```

---

**MES 2-12 (Sin nuevo pago):**

```
┌─────────────────────────────────────┐
│ CASH (Banco):        €0             │ ❌ No entra dinero nuevo
│ MRR:                 €100           │ ✅ Sigue contando
│ REVENUE (Mes 2):     +€100          │ ✅ Reconoces otro mes
└─────────────────────────────────────┘

Deferred Revenue: -€100 (cada mes)
```

**Cada mes reconoces €100 de los €1,200 que ya cobraste.**

---

### ¿Por Qué Importa?

**PELIGRO #1: Gastar todo el cash**

```
ERROR COMÚN:

Enero: Vendes €12,000 anuales
       → Tienes €12,000 en banco
       → Piensas: "Tengo €12k, puedo gastar €5k en ads"
       
Febrero: Vendes €0 nuevo
         → Tienes €7,000 en banco
         → Gastos: €3,000/mes
         → Te quedan €4,000
         
Marzo: Vendes €0 nuevo
       → Tienes €1,000 en banco
       → Gastos: €3,000/mes
       → TE QUEDAS SIN CASH
       
CONTABLEMENTE eres "rentable" (€1,000 revenue - €3,000 costs cada mes)
PERO NO TIENES CASH = QUIEBRAS
```

**LA REGLA:**

**Pagos anuales = NO son TUS ingresos de este mes.**
**Son ingresos distribuidos en 12 meses.**

---

## 📊 CONCEPTOS FINANCIEROS ESENCIALES

### 1. MRR (Monthly Recurring Revenue)

**Qué es:** Ingresos recurrentes mensuales.

**Cómo calcular:**
```
Cliente con plan mensual €29:
MRR = €29

Cliente con plan anual €348:
MRR = €348 / 12 = €29

Total MRR = Suma de todos los MRR
```

**Ejemplo:**
```
10 clientes × €29/mes = €290 MRR
5 clientes × €99/mes = €495 MRR
2 clientes × €348/año = €58 MRR (€348/12)

TOTAL MRR = €843
```

**Para qué sirve:** Medir crecimiento, proyectar futuro.

**NO ES:** Dinero en el banco este mes.

---

### 2. ARR (Annual Recurring Revenue)

**Qué es:** MRR × 12

```
€843 MRR × 12 = €10,116 ARR
```

**Para qué sirve:** Valoración, visión anual.

---

### 3. CASH (Efectivo)

**Qué es:** Dinero REAL en el banco. Ahora.

**Cómo ver:** Entras a tu banco, miras el saldo.

```
Banco: €5,234.56
= Eso es tu cash
```

**Para qué sirve:** Pagar gastos, sobrevivir.

**ES LO MÁS IMPORTANTE.**

---

### 4. Revenue (Ingresos Contables)

**Qué es:** Lo que contablemente puedes reconocer como ingreso este mes.

**Regla (SaaS):**
```
Pago mensual €29:
→ Revenue mes 1: €29 (todo el mes)

Pago anual €348:
→ Revenue mes 1: €29 (€348/12)
→ Revenue mes 2: €29
→ Revenue mes 3: €29
... hasta mes 12
```

**Para qué sirve:** Impuestos, contabilidad legal.

---

### 5. Deferred Revenue (Ingresos Diferidos)

**Qué es:** Dinero que cobraste pero aún no has "ganado" (servicio no prestado).

**Ejemplo:**
```
Cliente paga €1,200 anual el 1 enero:

Enero:
Cash: +€1,200 (cobrado)
Revenue: +€100 (reconocido)
Deferred Revenue: €1,100 (pendiente de reconocer)

Febrero:
Cash: €0 (ya cobrado)
Revenue: +€100
Deferred Revenue: €1,000 (va bajando)

Diciembre:
Deferred Revenue: €0 (ya reconociste todo)
```

**En balance:** Deferred Revenue = PASIVO (debes el servicio).

---

### 6. Churn (Cancelaciones)

**Qué es:** % clientes que cancelan por mes.

**Cómo calcular:**
```
Inicio mes: 100 clientes
Fin mes: 95 clientes (5 cancelaron)

Churn = 5 / 100 = 5%
```

**Meta:** <5% mensual (<50% anual).

**Impacto en MRR:**
```
€10,000 MRR con 5% churn mensual:
= Pierdes €500 MRR/mes por cancelaciones
= Necesitas €500 MRR nuevo SOLO para mantenerte
```

---

### 7. Runway (Pista de Aterrizaje)

**Qué es:** Cuántos meses puedes sobrevivir con tu cash actual.

**Cómo calcular:**
```
Cash en banco: €10,000
Gastos mensuales: €2,500
Revenue mensual: €1,500

Burn rate (pérdida neta): €2,500 - €1,500 = €1,000/mes

Runway = €10,000 / €1,000 = 10 meses
```

**CRÍTICO:** Monitorea esto SEMANALMENTE.

**Acción:** Si runway <6 meses → busca cash YA.

---

## 💸 CASH FLOW (Flujo de Caja)

### Qué es:

**Cash Flow = Cash que entra - Cash que sale**

**Simple pero VITAL.**

---

### Ejemplo Mes a Mes:

```
═══════════════════════════════════════════════════
MES 1 (Enero):
───────────────────────────────────────────────────
Cash inicio mes:           €5,000

ENTRADAS (Cash In):
  Nuevos clientes:         €2,900  (10 × €29 mensual)
  Renovaciones anuales:    €1,200  (1 cliente renueva)
  ───────────────────────
  Total Cash In:           €4,100

SALIDAS (Cash Out):
  Hosting (AWS):           -€150
  Software (tools):        -€200
  Stripe fees (3%):        -€123
  Tu salario:              -€2,000
  Contador:                -€100
  ───────────────────────
  Total Cash Out:          -€2,573

RESULTADO MES:
  Cash In - Cash Out:      €1,527

Cash fin mes:              €6,527 ✅ Creció

═══════════════════════════════════════════════════
```

---

### Cash Flow Positivo vs Negativo:

**Positivo:**
```
Cash In > Cash Out
= Estás creciendo
= Sostenible
```

**Negativo:**
```
Cash In < Cash Out
= Estás perdiendo dinero cada mes
= Runway disminuye
= Insostenible (eventualmente quiebras)
```

---

### El Problema de Pagos Anuales:

**Escenario peligroso:**

```
MES 1 (Enero):
Vendes €10,000 en planes anuales
Cash: +€10,000
Revenue: +€833 (€10k/12)

MES 2 (Febrero):
Vendes €0 nuevo
Cash: +€0
Revenue: +€833 (de planes Enero)
Gastos: -€3,000

Cash flow mes: -€3,000 ❌

MES 3 (Marzo):
Cash flow: -€3,000 ❌

MES 4 (Abril):
Cash flow: -€3,000 ❌
Cash restante: €1,000

MES 5 (Mayo):
QUIEBRAS (sin cash para gastos)
```

**Pero contablemente:**
```
Revenue cada mes: €833
Gastos cada mes: €3,000
Pérdida: -€2,167/mes

Pareces "rentable" en papel (si solo miras revenue recognition)
PERO te quedaste sin cash = MUERTO
```

---

## 📈 PROYECCIÓN FINANCIERA

### Template Mensual:

```
═══════════════════════════════════════════════════
PROYECCIÓN FINANCIERA - [MES/AÑO]
═══════════════════════════════════════════════════

INGRESOS (CASH):
  Nuevos MRR:              €X
  Planes anuales:          €Y
  Otros ingresos:          €Z
  ─────────────────────
  Total Cash In:           €X+Y+Z

GASTOS (CASH):
  Hosting/Infraestructura: €A
  Software/Tools:          €B
  Payment fees:            €C
  Marketing:               €D
  Salarios (si hay):       €E
  Tu salario:              €F
  Legal/Contador:          €G
  Otros:                   €H
  ─────────────────────
  Total Cash Out:          €A+B+C+D+E+F+G+H

NET CASH FLOW:             €Total_In - €Total_Out

─────────────────────────────────────────────────
CASH POSITION:
  Cash inicio mes:         €W
  Cash fin mes:            €W + Net_Cash_Flow
  
RUNWAY:
  Burn rate mensual:       €(avg gastos - avg ingresos)
  Meses restantes:         Cash / Burn_rate

═══════════════════════════════════════════════════

MÉTRICAS CLAVE:
  MRR:                     €M
  Churn:                   X%
  Nuevos clientes:         N
  CAC (costo adquirir):    €Z
  LTV (valor vida):        €Y

═══════════════════════════════════════════════════
```

**Hazlo en Excel/Google Sheets. Actualiza MENSUALMENTE.**

---

## 🏦 ENDEUDAMIENTO: CUÁNDO Y CÓMO

### ¿Cuándo tomar deuda?

**✅ BUENOS MOTIVOS:**

**1. Invertir en crecimiento con ROI claro**
```
Ejemplo:
Préstamo: €10,000
Usar en: Ads con CAC conocido
Payback: 6 meses
ROI positivo

SI tienes data que lo valida = OK
```

**2. Bridge loan (corto plazo)**
```
Ejemplo:
Runway: 2 meses
Esperando: Pago grande en 60 días
Préstamo: €5,000 para 3 meses

Temporal, salvas situación crítica = OK si seguro
```

**3. Evitar equity dilution**
```
Ejemplo:
Opción A: Vender 20% empresa por €50k
Opción B: Préstamo €30k

Si crees en crecimiento = préstamo mejor
```

---

**❌ MALOS MOTIVOS:**

**1. Cubrir pérdidas operacionales**
```
Gastas €5k/mes, ganas €2k/mes
Préstamo para cubrir déficit

= Solo retrasa inevitable
= No sostenible
= NO LO HAGAS
```

**2. Sin plan de repago**
```
"Ya veré cómo pago"
= Receta para desastre
```

**3. Expandir sin validación**
```
"Contrataré 5 personas con el préstamo"
Pero: No sabes si funcionará

= Alto riesgo
```

---

### Tipos de Deuda:

**1. Préstamo Personal (Amigos/Familia)**
- **Ventaja:** Flexible, sin interés (a veces)
- **Desventaja:** Riesgo relaciones
- **Recomendación:** Contrato escrito SIEMPRE

```
CONTRATO SIMPLE:

Yo, [Tu Nombre], recibo prestados €[Cantidad] de [Prestamista].

Términos:
• Cantidad: €[X]
• Interés: [%] anual (o 0% si familiar)
• Plazo: [X] meses
• Pagos: €[Y] mensuales
• Fecha inicio: [Fecha]

En caso de incumplimiento:
[Términos claros]

Firmado:
[Ambos]
[Fecha]
```

---

**2. Línea de Crédito Bancaria**
- **Ventaja:** Flexibilidad (usas lo que necesitas)
- **Desventaja:** Requiere garantías
- **Típico:** 10-20% interés anual

**Cómo funciona:**
```
Banco aprueba: €20,000 línea crédito
Usas: €5,000
Pagas interés sobre: €5,000 (no €20k)
Devuelves cuando puedas (dentro del plazo)
```

---

**3. Préstamo Bancario (Term Loan)**
- **Ventaja:** Cantidad fija, plan claro
- **Desventaja:** Rígido, garantías
- **Típico:** 8-15% interés anual

**Ejemplo:**
```
Préstamo: €20,000
Plazo: 3 años
Interés: 10% anual
Pago mensual: ~€645

Total repagar: ~€23,200
```

---

**4. Revenue-Based Financing**
- **Ventaja:** Pagas % de revenue (flexible)
- **Desventaja:** Puede ser caro
- **Típico:** Pagas 5-10% revenue hasta llegar a 1.3-1.5x prestado

**Ejemplo:**
```
Recibes: €30,000
Pagas: 8% de revenue mensual hasta €45,000 total

Si revenue €10k/mes:
→ Pagas €800/mes
→ Tardas ~56 meses (si revenue constante)

Si revenue crece:
→ Pagas más rápido pero más total
```

---

### Cómo Refleja en Contabilidad:

**DÍA 1 (Recibes préstamo):**
```
ACTIVOS:
  Cash (banco):            +€20,000 ✅

PASIVOS:
  Deuda por pagar:         +€20,000 ❌

NET: €0 (es neutral - no es "ingreso")
```

---

**CADA MES (Pagas cuota):**
```
Cuota: €645
  Interés: €167 (gasto)
  Principal: €478 (reduce deuda)

GASTOS:
  Interés préstamo:        +€167 (P&L)

PASIVOS:
  Deuda por pagar:         -€478 (balance)

CASH:
  Banco:                   -€645
```

---

**BALANCE FINAL (3 años después):**
```
ACTIVOS:
  Cash pagado:             -€23,200 total

PASIVOS:
  Deuda:                   €0 (pagada)

GASTOS (acumulado):
  Intereses:               €3,200 (costo total deuda)
```

---

### Ejemplo Real Completo:

```
SITUACIÓN:
MRR actual: €3,000
Runway: 4 meses (€8,000 cash, gastas €2,000/mes)
Crecimiento: +€500 MRR/mes

DECISIÓN: Pedir €10,000 préstamo

PLAN:
Usar en: Marketing (validado CAC €100, LTV €500)
Conseguir: 100 nuevos clientes
Nuevo MRR: +€2,900 (100 × €29)
Payback: 4 meses

RIESGO:
Si no funciona: Debes €10k + interés sin crecimiento

MITIGATION:
Test pequeño primero (€1,000)
Si funciona → escala con préstamo
```

---

## 📊 ESTADOS FINANCIEROS BÁSICOS

### 1. P&L (Profit & Loss) - Estado de Resultados

**Qué muestra:** Ingresos - Gastos = Ganancia/Pérdida

```
═══════════════════════════════════════════════════
P&L - [MES/AÑO]
═══════════════════════════════════════════════════

INGRESOS:
  Suscripciones reconocidas:     €5,000
  Otros ingresos:                €200
  ─────────────────────────────
  Total Ingresos:                €5,200

COSTO DE VENTAS (COGS):
  Hosting:                       €400
  Payment processing:            €156 (3%)
  ─────────────────────────────
  Total COGS:                    €556

MARGEN BRUTO:                    €4,644 (89%)

GASTOS OPERATIVOS:
  Marketing:                     €1,000
  Software/Tools:                €300
  Contador/Legal:                €200
  Salarios:                      €2,500
  Otros:                         €100
  ─────────────────────────────
  Total OpEx:                    €4,100

EBITDA:                          €544

Intereses (si hay deuda):        €100
Impuestos (estimado):            €0 (pérdidas anteriores)

NET INCOME (Ganancia/Pérdida):   €444 ✅
═══════════════════════════════════════════════════
```

**Interpretación:**
- Net Income positivo = Rentable (contablemente)
- Net Income negativo = Pérdidas

**PERO RECUERDA:** Rentable ≠ Cash positivo

---

### 2. Balance Sheet - Balance General

**Qué muestra:** Foto de tus activos y pasivos en un momento.

```
═══════════════════════════════════════════════════
BALANCE SHEET - [FECHA]
═══════════════════════════════════════════════════

ACTIVOS:
  Cash (banco):                  €15,000
  Cuentas por cobrar:            €500
  Equipos/Computadora:           €2,000
  ─────────────────────────────
  Total Activos:                 €17,500

PASIVOS:
  Deferred Revenue:              €8,000 (planes anuales)
  Deuda por pagar:               €5,000 (préstamo)
  Cuentas por pagar:             €300
  ─────────────────────────────
  Total Pasivos:                 €13,300

PATRIMONIO (Equity):
  Capital inicial:               €10,000
  Ganancias acumuladas:          -€5,800
  ─────────────────────────────
  Total Patrimonio:              €4,200

TOTAL (Activos = Pasivos + Patrimonio):  €17,500
═══════════════════════════════════════════════════
```

**Interpretación:**
- Activos > Pasivos = Patrimonio positivo ✅
- Activos < Pasivos = Patrimonio negativo ❌ (técnicamente insolvente)

---

### 3. Cash Flow Statement - Estado de Flujo de Caja

**Qué muestra:** Movimientos de cash (no contables).

```
═══════════════════════════════════════════════════
CASH FLOW STATEMENT - [MES]
═══════════════════════════════════════════════════

OPERATING ACTIVITIES (Operaciones):
  Cash cobrado de clientes:      €6,200
  Cash pagado a proveedores:     -€1,500
  Cash pagado salarios:          -€2,500
  ─────────────────────────────
  Net Cash from Operations:      €2,200

INVESTING ACTIVITIES (Inversiones):
  Compra equipos:                -€500
  ─────────────────────────────
  Net Cash from Investing:       -€500

FINANCING ACTIVITIES (Financiamiento):
  Préstamo recibido:             €10,000
  Pago préstamo (principal):     -€400
  ─────────────────────────────
  Net Cash from Financing:       €9,600

NET CHANGE IN CASH:              €11,300

Cash inicio mes:                 €8,000
Cash fin mes:                    €19,300 ✅
═══════════════════════════════════════════════════
```

**Este es EL MÁS IMPORTANTE para sobrevivir.**

---

## 🚨 RED FLAGS FINANCIERAS

### Señales de Peligro:

#### 🔴 CRÍTICO (Actúa YA):

**1. Runway <3 meses**
```
Action: Corta gastos + busca cash + acelera ventas
```

**2. Churn >10% mensual**
```
= Pierdes todos los clientes en 10 meses
Action: Arregla producto/onboarding YA
```

**3. Cash flow negativo creciente**
```
Mes 1: -€1k
Mes 2: -€2k
Mes 3: -€3k

= Acelerando hacia quiebra
Action: Corta gastos inmediatamente
```

**4. Gastas más que ingresas (consistentemente)**
```
6 meses seguidos con pérdidas
Action: Revisa modelo de negocio
```

---

#### 🟠 PREOCUPANTE (Monitorea):

**1. Runway 3-6 meses**
```
No crítico pero pronto
Action: Plan para conseguir cash
```

**2. Churn 5-10%**
```
Alto pero manejable
Action: Identifica por qué cancelan
```

**3. CAC > LTV**
```
Gastas más en adquirir que ganas
Action: Mejora retención o reduce CAC
```

**4. Deferred revenue < 3 meses de gastos**
```
Poca reserva de planes anuales
Action: Push planes anuales más
```

---

## 💡 ERRORES COMUNES DE FOUNDERS

### Error #1: Confundir MRR con Cash

**Síntoma:**
"Tengo €10k MRR, puedo gastar €8k/mes"

**Problema:**
MRR ≠ Cash in bank
Especialmente con planes anuales

**Fix:**
Mira cash flow, no MRR

---

### Error #2: No Separar Cuentas

**Síntoma:**
Cuenta personal = Cuenta negocio

**Problema:**
- Mezclas gastos
- Pesadilla contable
- Problemas legales

**Fix:**
Cuenta bancaria business desde día 1

---

### Error #3: No Trackear Gastos

**Síntoma:**
"No sé en qué gasté €2,000 este mes"

**Problema:**
No puedes optimizar lo que no mides

**Fix:**
Software contable (QuickBooks, Xero, Wave)

---

### Error #4: Salario Muy Alto (o Muy Bajo)

**Síntoma:**
Te pagas €5k/mes con €3k MRR

**Problema:**
Cash flow negativo = muerte

**Fix:**
Salario = Lo mínimo para sobrevivir hasta rentable

---

### Error #5: No Reservar para Impuestos

**Síntoma:**
Gastas todo, llega declaración, no tienes cash

**Problema:**
Debes €10k en impuestos, tienes €2k

**Fix:**
Separa 25-30% ingresos para impuestos (cuenta aparte)

---

### Error #6: Ignorar Runway

**Síntoma:**
"Ya veré qué pasa"

**Problema:**
Te quedas sin cash de sorpresa

**Fix:**
Calcula runway SEMANALMENTE

---

## 📋 CHECKLIST FINANCIERA MENSUAL

### Cada Mes, Hacer:

- [ ] Actualizar projection spreadsheet
- [ ] Calcular MRR actual
- [ ] Calcular churn rate
- [ ] Revisar cash flow statement
- [ ] Calcular runway
- [ ] Revisar P&L con contador
- [ ] Separar % para impuestos
- [ ] Identificar gastos innecesarios
- [ ] Proyectar próximos 3 meses

---

### Cada Trimestre:

- [ ] Revisar balance sheet completo
- [ ] Reunión con contador (tax planning)
- [ ] Evaluar necesidad de financiamiento
- [ ] Revisar pricing strategy
- [ ] Comparar proyecciones vs realidad

---

### Cada Año:

- [ ] Declaración de impuestos (con contador)
- [ ] Auditoría interna
- [ ] Revisión estrategia financiera
- [ ] Actualizar proyección 12 meses

---

## 🎯 MÉTRICAS CLAVE A TRACKEAR

### Diarias:
- Cash in bank

### Semanales:
- New MRR
- Churn MRR
- Runway

### Mensuales:
- Total MRR
- Churn rate
- Net MRR growth
- Cash flow
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)
- Burn rate

### Trimestrales:
- Profitability (P&L)
- Balance sheet health
- Debt/equity ratio (si hay deuda)

---

## 💼 HERRAMIENTAS RECOMENDADAS

### Contabilidad:
- **Wave** (gratis para básico)
- **QuickBooks** (€15-40/mes)
- **Xero** (€20-50/mes)

### Proyecciones:
- **Google Sheets** (gratis, suficiente)
- **Excel** (si lo prefieres)
- **Causal** (€50+/mes, fancy)

### Métricas SaaS:
- **ChartMogul** (€100+/mes)
- **Baremetrics** (€100+/mes)
- **DIY en Sheets** (gratis, más trabajo)

### Banco:
- **Cuenta business** (tu banco tradicional)
- **Wise Business** (internacional, barato)
- **Revolut Business** (alternativa)

---

## 🎓 APRENDER MÁS

### Recursos:

**Libros:**
- "Financial Intelligence" - Karen Berman
- "Profit First" - Mike Michalowicz (metodología cash)

**Blogs:**
- SaaS Financial Operations (Google it)
- Christoph Janz (SaaS metrics)

**Cursos:**
- Coursera: "Financial Management" basics

**Contador:**
- **CONTRATA UNO** (€100-300/mes, vale la pena)

---

## ✅ RESUMEN EJECUTIVO

### Las Reglas de Oro:

**1. Cash is King**
```
MRR es vanidad
Cash es realidad
Sin cash = muerto
```

**2. Revenue Recognition**
```
Pago anual €1,200 ≠ €1,200 revenue
= €100/mes × 12 meses
```

**3. Track Runway**
```
<3 meses = crisis
3-6 meses = preocupante
6-12 meses = ok
12+ meses = comfortable
```

**4. Don't Overspend**
```
Gastos < Ingresos (cash)
= Sostenible
```

**5. Separate Money**
```
Business ≠ Personal
Impuestos separados
```

**6. Professional Help**
```
Contador desde día 1
€100-300/mes
Evita errores de €10k+
```

---

**BOTTOM LINE:**

**Puedes tener 100 clientes y quebrar.**
**Puedes ser "rentable" en papel y quebrar.**

**Solo importa: ¿Tienes cash para el próximo mes?**

**Monitorea cash flow como tu vida depende de ello.**
**Porque literalmente así es.**

---

**CONTRATA UN CONTADOR. EN SERIO.**
