# DOCUMENTATION STRUCTURE - SAMPLIT

## 📚 DOCUMENTATION SITE STRUCTURE

### Recommended URL: `docs.samplit.com`

```
docs.samplit.com/
├── Getting Started
├── Installation
├── Creating Tests
├── Reading Results
├── Integrations
├── API Reference
├── Troubleshooting
├── Best Practices
└── FAQ
```

---

## 🚀 GETTING STARTED

### Page: `docs.samplit.com/getting-started`

```markdown
# Getting Started with Samplit

Welcome! This guide will have you running your first A/B test in 
10 minutes.

## What You'll Need

- A website with at least 500 visitors/month
- Admin access to your website (to install tracker)
- Something you want to test (headline, button, etc.)

## Quick Start (5 Steps)

### Step 1: Create Account
1. Go to samplit.com/signup
2. Enter email and password
3. Verify your email

**⏱️ Time: 2 minutes**

### Step 2: Install Tracker
Choose your platform:

**WordPress/Shopify (Easy):**
- Install our plugin
- [WordPress Guide] [Shopify Guide]

**Other Platforms (5 minutes):**
- Copy snippet from dashboard
- Paste before closing `</head>` tag
- [Detailed Installation Guide]

**⏱️ Time: 2-5 minutes**

### Step 3: Verify Installation
1. Dashboard → Settings → Installation
2. Click "Test Installation"
3. ✅ Should show "Connected"

**⏱️ Time: 1 minute**

### Step 4: Create Your First Test
1. Dashboard → New Experiment
2. Enter page URL
3. Create 2-3 variants
4. Define conversion goal
5. Click "Start Test"

[Detailed: Creating Tests Guide]

**⏱️ Time: 5 minutes**

### Step 5: Wait for Results
- Check dashboard daily
- Wait for 95% confidence
- Implement winner

**⏱️ Time: 3-7 days** (depends on traffic)

---

## Next Steps

- [Read: How to Interpret Results]
- [Read: What to Test First]
- [Watch: Video Tutorial] (5 min)

## Need Help?

- 📧 Email: support@samplit.com
- 💬 Chat: Bottom right of dashboard
- 📖 Docs: You're here!
- 🎥 Video Tutorials: [Link]
```

---

## 🔧 INSTALLATION

### Page: `docs.samplit.com/installation`

```markdown
# Installation Guide

## Overview

Samplit requires a small JavaScript snippet on your site to track 
visitors and serve variants.

**Installation time:**
- WordPress/Shopify: 2 minutes (plugin)
- Other platforms: 5 minutes (manual)

---

## Option 1: Plugin (Recommended)

### WordPress

1. **Download Plugin**
   - Dashboard → Settings → WordPress
   - Download `samplit-wp.zip`

2. **Install**
   - WordPress Admin → Plugins → Add New
   - Upload `samplit-wp.zip`
   - Activate

3. **Configure**
   - Settings → Samplit
   - Enter your API key (copy from dashboard)
   - Save

**✅ Done!** Verify below.

---

### Shopify

1. **Install App**
   - Dashboard → Settings → Shopify
   - Click "Install on Shopify"
   - Authorize app

2. **Configure**
   - App will auto-configure
   - No additional steps

**✅ Done!** Verify below.

---

## Option 2: Manual Installation

### Step 1: Get Your Snippet

Dashboard → Settings → Installation

Copy this code:

```html
<script>
  !function(s,a,m,p,l,i,t){/* Samplit snippet */}
  samplit.init('YOUR_API_KEY');
</script>
```

### Step 2: Add to Your Site

**Add before closing `</head>` tag** on every page you want to test.

#### Common Platforms:

**Webflow:**
- Project Settings → Custom Code → Head Code
- Paste snippet
- Publish

**Wix:**
- Settings → Custom Code
- Add to "Head" section
- Apply to all pages

**Squarespace:**
- Settings → Advanced → Code Injection
- Paste in Header
- Save

**Custom Site:**
- Edit your template/layout file
- Add before `</head>`
- Deploy

**Single Page App (React/Vue/Angular):**
- Add to `public/index.html` in `<head>`
- Or import via npm (see API docs)

---

## Verify Installation

1. Dashboard → Settings → Installation
2. Click "Test Installation"
3. Open your website in another tab
4. Return to dashboard

**Success:** ✅ "Tracker detected"
**Failure:** ❌ "No connection"

### Troubleshooting Verification:

**"No connection" error:**
- Wait 60 seconds and retry
- Check snippet was pasted correctly
- Check if `</head>` tag exists
- Clear cache (browser and site)
- Check browser console for errors

Still having issues? → [Troubleshooting Guide]

---

## Advanced Options

### npm Package (React/Vue/Next.js)

```bash
npm install @samplit/client
```

```javascript
import Samplit from '@samplit/client';

Samplit.init('YOUR_API_KEY');
```

[Full API Documentation]

---

### Google Tag Manager

1. GTM → New Tag
2. Custom HTML
3. Paste snippet
4. Trigger: All Pages
5. Publish

---

## Security Notes

- Snippet is asynchronous (doesn't block page load)
- Served via CDN (fast globally)
- GDPR compliant
- No cookies without consent

---

## Next Steps

✅ Installation complete
→ [Create Your First Test]
```

---

## 🧪 CREATING TESTS

### Page: `docs.samplit.com/creating-tests`

```markdown
# Creating Tests

## Overview

A test (experiment) compares 2+ variants of a page element to see 
which performs better.

---

## Quick Create

### Step 1: New Experiment

Dashboard → **New Experiment**

### Step 2: Basic Info

**Name:** Descriptive name (e.g., "Homepage hero headline")
**Page URL:** Where to run test (e.g., `https://yoursite.com`)

### Step 3: Create Variants

**Variant A (Control):** Original version
**Variant B:** Changed version
**Variant C (optional):** Another version

#### Example:

**Element:** Headline
- Variant A: "Stop wasting traffic on losing variants"
- Variant B: "Get 3x faster A/B test results"
- Variant C: "Adaptive testing that actually works"

### Step 4: Define Conversion

**What counts as success?**

Common goals:
- Click button (e.g., "Sign up")
- Visit page (e.g., `/thank-you`)
- Form submission
- Add to cart
- Purchase

**Example:** Click button with ID `#cta-signup`

### Step 5: Traffic Allocation

**Start:** Let Samplit decide (recommended)
**Advanced:** Set manual % split

### Step 6: Launch

Click **Start Test**

✅ Test is now live!

---

## Visual Editor vs Code

### Visual Editor (Easy)

1. Enter page URL
2. Click "Visual Editor"
3. Click element to change
4. Edit text/style
5. Save as variant

**Best for:**
- Text changes
- Simple styling
- Button colors
- Image swaps

### Code Mode (Advanced)

Write custom JavaScript to modify page.

```javascript
// Example: Change headline
document.querySelector('.hero h1').textContent = 'New headline';
```

**Best for:**
- Complex changes
- Multiple elements
- Dynamic content
- Full redesigns

---

## Conversion Goals

### Click Element

**CSS Selector:**
```
#signup-button
.cta-primary
button[type="submit"]
```

**When to use:** Button clicks, link clicks

---

### Page Visit

**URL:**
```
/thank-you
/checkout/success
/dashboard
```

**When to use:** Sign ups, purchases, navigation

---

### Custom Event

**Event name:**
```
purchase_completed
form_submitted
video_watched
```

**Requires:** Add event tracking code

```javascript
samplit.track('purchase_completed', { value: 99.99 });
```

---

## Best Practices

### ✅ DO:

**Start Simple:**
- 2-3 variants max
- One element at a time
- Clear hypothesis

**Test Meaningful Changes:**
- Headlines that change value prop
- CTAs that change action
- Designs that change layout
- NOT "red vs blue button" as first test

**Define Clear Goal:**
- One primary conversion
- Measurable outcome
- Business impact

**Give It Time:**
- Wait for 95% confidence
- Minimum 100 conversions
- At least 5-7 days

### ❌ DON'T:

**Too Complex:**
- 5+ variants (needs too much traffic)
- Multiple elements changing
- Subtle differences users won't notice

**Change Mid-Test:**
- Don't edit variants during test
- Don't change goal
- Don't add more variants

**Stop Too Early:**
- Don't trust results at 60% confidence
- Don't stop at 50 conversions
- Don't stop after 2 days

**Test Everything:**
- Focus on high-impact pages
- Prioritize (use PIE framework)
- Don't run 10 tests at once (when starting)

---

## Traffic Requirements

**Minimum recommended:**
- 500 visitors/month to test page
- 50 conversions expected per variant

**Calculator:**
Use our [Traffic Calculator] to estimate time needed.

**Example:**
- 2,000 visitors/month
- 3% conversion rate = 60 conversions
- 2 variants
- Result: ~10 days to 95% confidence

---

## Next Steps

Test created! Now what?

1. [Verify test is running] - Check dashboard
2. [Monitor progress] - Check daily
3. [Read results] - When confident
4. [Implement winner] - Deploy best variant

---

## Troubleshooting

**Test not running:**
- Check installation is verified
- Check page URL is correct
- Check selector finds element
- View browser console for errors

**No visitors showing:**
- Wait 1 hour for data
- Check page has traffic
- Verify tracker installed on that page

[Full Troubleshooting Guide]
```

---

## 📊 READING RESULTS

### Page: `docs.samplit.com/reading-results`

```markdown
# Reading Results

## Dashboard Overview

Your test dashboard shows:

```
╔════════════════════════════════════════════╗
║  Homepage Hero Test                        ║
║  Running · 5 days                          ║
╠════════════════════════════════════════════╣
║  Variant A (Control)                       ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  67%  ║
║  1,240 views · 87 conversions · 7.0% CR    ║
║                                            ║
║  Variant B                                 ║
║  ━━━━━━━━━━━━━━━  33%                     ║
║  623 views · 51 conversions · 8.2% CR      ║
║                                            ║
║  Confidence: 89% → Keep running           ║
╚════════════════════════════════════════════╝
```

---

## Key Metrics Explained

### Impressions
**Number of visitors who saw each variant.**

**Why not 50/50?**
Samplit's adaptive algorithm gives more traffic to better-performing 
variants. This is NORMAL and GOOD.

---

### Conversions
**Number who completed your goal** (clicked button, visited page, etc.)

---

### Conversion Rate (CR)
**Percentage who converted.**

Formula: `(Conversions / Impressions) × 100`

Example: `(51 / 623) × 100 = 8.2%`

---

### Confidence
**Statistical certainty that the difference is real, not luck.**

- **< 80%:** Not enough data yet. Keep running.
- **80-94%:** Promising, but wait for more data.
- **≥ 95%:** ✅ Result is statistically significant!
- **99%+:** Very strong result.

**Rule:** Wait for ≥95% confidence before making decisions.

---

### Traffic Distribution
**% of visitors sent to each variant.**

Samplit automatically adjusts this. Winning variants get more traffic.

**Why this matters:**
Reduces "wasted" traffic on losing variants while still gathering 
enough data.

---

## When to Stop a Test

### ✅ Stop When:

**All 3 conditions met:**
1. ✅ Confidence ≥ 95%
2. ✅ Total conversions ≥ 100 (across all variants)
3. ✅ Running ≥ 5-7 days (to account for day-of-week effects)

**Then:** Implement winner

---

### ⏸️ Keep Running If:

- Confidence < 95%
- < 100 total conversions
- < 5 days running
- Major traffic fluctuations this week

**Patience = accurate results**

---

### 🛑 Stop Early If:

**Rare cases:**
- Test misconfigured (fix and restart)
- Business priority changed
- Unintended negative impact observed

**Exception:** You can stop a clearly losing test early to minimize 
damage, but can't trust winning tests until 95% confidence.

---

## Interpreting Results

### Scenario 1: Clear Winner

```
Variant A: 3.2% CR
Variant B: 4.8% CR (+50%)
Confidence: 98%
```

**Action:** Implement Variant B. Celebrate 🎉

---

### Scenario 2: No Clear Winner

```
Variant A: 3.2% CR  
Variant B: 3.4% CR (+6%)
Confidence: 72%
```

**Action:** 
- Keep running (may reach significance)
- OR stop and try bigger changes
- Small differences need more data

---

### Scenario 3: Loser

```
Variant A: 3.2% CR
Variant B: 2.1% CR (-34%)
Confidence: 95%
```

**Action:** 
- Keep Variant A (original)
- Learn why B failed
- Try different approach

**Don't be discouraged.** Failed tests teach you as much as winners.

---

### Scenario 4: Multi-Variant

```
Variant A: 3.2% CR
Variant B: 3.8% CR (+19%)
Variant C: 4.5% CR (+41%)
Confidence: 94%
```

**Action:**
- Variant C is leading
- Wait for 95%+ confidence
- Then implement C

---

## Common Questions

### "Why is traffic not 50/50?"

**Answer:** Samplit adapts traffic to maximize conversions while 
testing. Better performers get more traffic. This is the core 
feature!

### "Can I trust 85% confidence?"

**Answer:** No. Industry standard is 95%. Below that, too much 
chance of false positive.

### "Test has been running 2 weeks, still 80% confidence"

**Possible causes:**
- Low traffic
- Small difference between variants  
- High variance in results

**Solutions:**
- Give it more time
- Try bigger changes
- Check traffic is being tracked

### "Variant B was winning, now Variant A is winning"

**Answer:** Normal fluctuation, especially early on. This is why 
we wait for 95% confidence. Results stabilize with more data.

### "Can I run multiple tests on same page?"

**Answer:** Not recommended. Tests can interfere. Run sequentially 
for clean results.

---

## Statistical Notes

### P-Value

Samplit shows confidence %, which relates to p-value:

- 95% confidence = p-value 0.05
- 99% confidence = p-value 0.01

**Lower p-value = stronger result**

### Bayesian vs Frequentist

Samplit uses adaptive algorithms that incorporate Bayesian principles 
while maintaining frequentist rigor for reporting.

**In practice:** You get faster results with reliable statistics.

---

## Export Results

**Dashboard → Export**

Download CSV with:
- All metrics
- Daily breakdown
- Variant details

Use for:
- Presentations
- Reporting
- Further analysis

---

## Next Steps

✅ Results interpreted
→ [Implement Winner]
→ [What to Test Next]
→ [Case Studies]
```

---

## 🔌 INTEGRATIONS

### Page: `docs.samplit.com/integrations`

```markdown
# Integrations

## WordPress

**Plugin:** Samplit for WordPress

**Features:**
- One-click installation
- Visual test editor
- No code required

[Installation Guide] [Download Plugin]

---

## Shopify

**App:** Samplit for Shopify

**Features:**
- Auto-install tracker
- Theme compatibility
- Checkout testing (Shopify Plus)

[Installation Guide] [Install from Shopify App Store]

---

## WooCommerce

Use WordPress plugin (above).

**Special features:**
- Product page testing
- Cart page testing
- Checkout testing

---

## Webflow

**Integration:** Manual snippet

**Steps:**
1. Project Settings → Custom Code
2. Add snippet to Head
3. Publish

[Full Guide]

---

## Google Tag Manager

**Integration:** Custom HTML tag

**Steps:**
1. New Tag → Custom HTML
2. Paste snippet
3. Trigger: All Pages
4. Publish

[Full Guide]

---

## Zapier

**Coming soon**

Automate workflows:
- Test completes → Slack notification
- Winner found → Update CMS
- New subscriber → Add to test audience

---

## API Integration

For developers:

[API Documentation →]

---

## Request Integration

Need integration with another platform?

[Request Here] - We prioritize based on demand.
```

---

## 🔥 TROUBLESHOOTING

### Page: `docs.samplit.com/troubleshooting`

```markdown
# Troubleshooting

## Installation Issues

### "Test Installation" shows not connected

**Check:**
1. ✅ Snippet pasted correctly
2. ✅ Snippet in `<head>` (not `<body>`)
3. ✅ Saved and published changes
4. ✅ Cleared browser cache
5. ✅ Cleared site cache (if using caching plugin)

**Test:**
- Open your site
- Open browser console (F12)
- Look for: `Samplit initialized`
- If not there, snippet not loading

**Still stuck?**
Send screenshot of:
- Where you pasted snippet
- Browser console
To: support@samplit.com

---

### Snippet won't save (WordPress)

**Cause:** Security plugin blocking

**Fix:**
- Temporarily disable security plugin
- Save snippet
- Re-enable security plugin
- Whitelist Samplit domain in security settings

---

## Test Issues

### Test not running (shows "Draft")

**Check:**
1. ✅ Clicked "Start Test" button
2. ✅ Installation verified
3. ✅ Page URL correct

**Still draft?**
- Dashboard → Test → Start Test

---

### No visitors showing in test

**Check:**
1. ✅ Test is "Running" (not "Draft")
2. ✅ Page URL matches exactly
   - Include/exclude `www`
   - Include/exclude trailing `/`
3. ✅ Page actually has traffic
4. ✅ Wait 1-2 hours for data

**Test:** Visit your page, check dashboard after 5 min.

---

### Variant not showing on page

**Check:**
1. ✅ CSS selector is correct
   - Open browser console
   - Type: `document.querySelector('YOUR_SELECTOR')`
   - Should return element
2. ✅ Element loads before snippet runs
   - For dynamic content, use callback
3. ✅ No JavaScript errors blocking

**Debug Mode:**
- Dashboard → Test → Settings → Debug Mode ON
- Visit page
- Check console for Samplit messages

---

### Conversion not tracking

**Check:**
1. ✅ Conversion goal configured
2. ✅ Goal selector/URL correct
3. ✅ Test the conversion yourself
4. ✅ Check dashboard after 10 min

**For click goals:**
- Inspect element
- Verify CSS selector matches

**For page visit goals:**
- Check exact URL match
- Include query params if needed

---

### Test Results Issues

### Confidence stuck at low %

**Causes:**
- Small difference between variants (need more data)
- Low traffic volume
- High variability

**Solutions:**
- Be patient (can take weeks for low traffic)
- Try bigger changes between variants
- Increase traffic to test page

---

### Traffic distribution seems wrong

**Remember:** Samplit is ADAPTIVE.

- Better performers get more traffic
- This is intentional
- Not 50/50 (that's the point!)

**Concern?**
Check in Dashboard → Test → Distribution
Should see chart explaining allocation.

---

## Performance Issues

### Page loads slowly after installing

**Rare, but check:**
- Snippet async? (should be)
- CDN accessible? (ping cdn.samplit.com)
- Other slow scripts conflicting?

**Our snippet:**
- Asynchronous
- < 30KB
- CDN-delivered
- Shouldn't impact load time

**Test:** Use PageSpeed Insights before/after.

---

### Browser console errors

**Common errors:**

**"Samplit is not defined"**
- Snippet not loaded
- Ad blocker blocking
- Wrong API key

**"Cannot find element"**
- CSS selector wrong
- Element loads late (use callback)

**"CORS error"**
- Should not happen with our CDN
- Report to support

---

## Data & Account Issues

### Missing experiments data

**Check:**
- Date range filter
- Archived experiments (toggle to show)
- Account switched? (if multiple)

**Data lost?**
We back up daily. Contact support to restore.

---

### Cannot log in

**Try:**
- Reset password
- Check email for verification
- Different browser/device
- Clear cookies

**Still locked out?**
support@samplit.com

---

### Billing issue

- Incorrect charge
- Card declined
- Can't upgrade

**Contact:**
billing@samplit.com
(Response in 24h)

---

## Still Need Help?

### 📧 Email Support
support@samplit.com
Response: < 24h (Starter), < 12h (Pro)

### 💬 Live Chat
Dashboard → Chat icon (bottom right)
Available: Business hours (CET)

### 📖 More Docs
[Full Documentation]

### 🎥 Video Tutorials
[Video Library]

### 🐛 Report Bug
bugs@samplit.com
Include:
- Browser & version
- Steps to reproduce
- Screenshots
- Console errors
```

---

## ⚡ API REFERENCE

### Page: `docs.samplit.com/api`

```markdown
# API Reference

## Overview

Samplit API allows programmatic control of experiments, data access, 
and custom integrations.

**Base URL:** `https://api.samplit.com/v1`

**Authentication:** API Key (Bearer token)

---

## Authentication

### Get API Key

Dashboard → Settings → API Keys → Create Key

### Request Headers

```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

---

## Endpoints

### List Experiments

**GET** `/experiments`

**Response:**
```json
{
  "data": [
    {
      "id": "exp_abc123",
      "name": "Homepage Hero Test",
      "status": "running",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

---

### Get Experiment

**GET** `/experiments/{id}`

**Response:**
```json
{
  "id": "exp_abc123",
  "name": "Homepage Hero Test",
  "status": "running",
  "variants": [...],
  "results": {...}
}
```

---

### Create Experiment

**POST** `/experiments`

**Body:**
```json
{
  "name": "Hero Test",
  "page_url": "https://example.com",
  "variants": [
    { "name": "A", "changes": [...] },
    { "name": "B", "changes": [...] }
  ],
  "goal": {
    "type": "click",
    "selector": "#cta-button"
  }
}
```

---

[Full API Documentation →]
```

---

## 🎯 BEST PRACTICES

### Page: `docs.samplit.com/best-practices`

```markdown
# Best Practices

## What to Test First

### High-Impact Pages
1. Homepage
2. Pricing page
3. Signup/Checkout
4. Key landing pages

### High-Impact Elements
1. Headlines
2. CTA buttons
3. Value propositions
4. Forms (# of fields)
5. Social proof placement

---

## PIE Framework

Prioritize tests using:

**P**otential (1-10): How much can this improve?
**I**mportance (1-10): How critical is this page?
**E**ase (1-10): How easy to implement?

**Score = (P + I + E) / 3**

Run tests with highest PIE score first.

---

## Test Design

### ✅ Good Test
- 2-3 variants
- One clear change
- Measurable goal
- Realistic to implement

### ❌ Bad Test
- 5+ variants
- Multiple changes at once
- Vague goal
- Can't implement winner

---

## Statistical Rigor

### Always:
- Wait for 95% confidence
- Minimum 100 conversions
- Run 5-7+ days (account for weekly patterns)

### Never:
- Stop at 80% confidence
- Trust results with < 50 conversions
- Stop after 2 days
- Change test mid-run

---

[Full Best Practices Guide]
```

---

## 📋 DOCUMENTATION MAINTENANCE

### Update Schedule:

- **After each feature:** Update relevant docs
- **Monthly:** Review for accuracy
- **Quarterly:** Check all links work
- **Annually:** Major refresh

### Track Changes:

Keep changelog:
```
## 2025-10-15
- Added: React integration guide
- Updated: API authentication section
- Fixed: Broken link in troubleshooting

## 2025-09-01
- Added: Video tutorials
- Updated: Installation for Shopify
```

### Versioning:

If API changes:
- Keep old version docs (`/api/v1`)
- Add new version (`/api/v2`)
- Deprecation notice (6 months warning)

---

## 🔍 SEARCH & NAVIGATION

### Must-Have:
- **Search bar** (Algolia DocSearch recommended)
- **Breadcrumbs** (Home > Installation > WordPress)
- **Next/Previous** navigation
- **Table of contents** (right sidebar)
- **Related articles** (bottom of page)

### Helpful:
- **Copy code buttons**
- **Estimated read time**
- **"Was this helpful?" feedback
- **Last updated** date on each page

---

## 📊 ANALYTICS

### Track:
- Most visited pages
- Search queries (what people look for)
- "Not helpful" feedback
- Time on page
- Bounce rate

**Use this data** to improve docs where users struggle most.
