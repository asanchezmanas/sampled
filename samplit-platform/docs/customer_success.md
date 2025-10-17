# CUSTOMER SUCCESS FRAMEWORK - SAMPLIT

## 🎯 CUSTOMER SUCCESS GOALS

### Primary Metrics:
- **Activation Rate:** % who create first test within 7 days
- **Retention:** % still active after 30/60/90 days
- **Churn Rate:** % canceling per month (target: <5%)
- **NPS Score:** Net Promoter Score (target: >40)
- **Time to Value:** Days until first successful test

### Success Definition:
**Successful customer = Created ≥3 tests + achieved ≥1 winning test**

---

## 📋 ONBOARDING CHECKLIST

### Customer's First 7 Days

#### ✅ Day 0: Signup
**Automated:**
- [ ] Welcome email sent
- [ ] Account created in dashboard
- [ ] Trial started (14 days)

**Customer should complete:**
- [ ] Email verified
- [ ] Basic profile filled (optional)

---

#### ✅ Day 0-1: Installation
**Goal:** Get tracker installed

**Automated:**
- [ ] Email: "Install in 5 minutes" (Day +1 if not done)
- [ ] In-app prompt: "Complete installation"

**Customer should complete:**
- [ ] Tracker installed
- [ ] Installation verified (green checkmark)

**Trigger:** If not done in 24h → Send reminder email
**Escalate:** If not done in 3 days → Support reaches out

---

#### ✅ Day 2-3: First Test
**Goal:** Create and launch first test

**Automated:**
- [ ] Email: "Create your first test"
- [ ] In-app guide: "3 steps to your first test"
- [ ] Success metrics: Time to first test

**Customer should complete:**
- [ ] First test created
- [ ] Test launched (status: Running)

**Trigger:** If not done in 5 days → Send "Need help?" email

---

#### ✅ Day 4-7: Monitor Results
**Goal:** Understand dashboard, check progress

**Automated:**
- [ ] Email: "How to read your results"
- [ ] Notification: When test reaches 50% confidence

**Customer should:**
- [ ] Log in to check results
- [ ] Understand metrics

---

#### ✅ Day 7+: Complete First Test
**Goal:** Get to 95% confidence, implement winner

**Automated:**
- [ ] Notification: Test reached 95% confidence
- [ ] Email: "Your first test results"
- [ ] Prompt: "Create next test?"

**Customer should:**
- [ ] Review results
- [ ] Implement winner
- [ ] Create second test

---

### Onboarding Success Rates (Benchmarks)

**Target milestones:**
- Day 1: 80% install tracker
- Day 3: 60% create first test
- Day 7: 40% launch first test
- Day 14: 30% complete first test (95% confidence)

**If below target:** Review onboarding flow, improve friction points

---

## 🎓 HELP CENTER STRUCTURE

### URL: `help.samplit.com`

```
Help Center
├── Getting Started
│   ├── Quick Start Guide
│   ├── Video Tutorials
│   └── First Test Walkthrough
│
├── Account & Billing
│   ├── Plans & Pricing
│   ├── Upgrade/Downgrade
│   ├── Payment Methods
│   ├── Invoices & Receipts
│   └── Cancel Subscription
│
├── Installation
│   ├── WordPress
│   ├── Shopify
│   ├── Manual Installation
│   ├── Verify Installation
│   └── Troubleshooting
│
├── Creating Tests
│   ├── Create Experiment
│   ├── Visual Editor
│   ├── Code Mode
│   ├── Conversion Goals
│   └── Best Practices
│
├── Understanding Results
│   ├── Dashboard Overview
│   ├── Metrics Explained
│   ├── Statistical Significance
│   ├── When to Stop Test
│   └── Export Data
│
├── Integrations
│   ├── WordPress Plugin
│   ├── Shopify App
│   ├── Google Tag Manager
│   ├── API Access
│   └── Request Integration
│
├── Troubleshooting
│   ├── Installation Issues
│   ├── Test Not Running
│   ├── Conversion Not Tracking
│   ├── Performance Issues
│   └── Common Errors
│
└── Legal & Privacy
    ├── Terms of Service
    ├── Privacy Policy
    ├── GDPR Compliance
    └── Data Processing
```

---

### Article Template:

```markdown
# [Article Title]

**2 min read** · Last updated: [Date]

## Problem
[Describe what user is trying to do or problem they're facing]

## Solution
[Step-by-step solution]

### Step 1: [Action]
[Screenshot]
[Detailed explanation]

### Step 2: [Action]
[Screenshot]
[Detailed explanation]

## Common Issues
**Issue:** [Common problem]
**Fix:** [Solution]

## Related Articles
- [Link to related article 1]
- [Link to related article 2]

## Still need help?
[Contact Support Button]

---
Was this article helpful? [👍 Yes] [👎 No]
```

---

## 📞 SUPPORT WORKFLOWS

### Support Channels by Plan:

| Channel | Free | Starter | Professional | Enterprise |
|---------|------|---------|--------------|------------|
| Help Center | ✅ | ✅ | ✅ | ✅ |
| Email | ❌ | ✅ | ✅ | ✅ |
| Chat (in-app) | ❌ | ❌ | ✅ | ✅ |
| Priority Support | ❌ | ❌ | ✅ | ✅ |
| Phone | ❌ | ❌ | ❌ | ✅ |
| Dedicated CSM | ❌ | ❌ | ❌ | ✅ |

---

### SLA (Service Level Agreement)

#### Response Time:

| Priority | Description | Starter | Professional | Enterprise |
|----------|-------------|---------|--------------|------------|
| P1 - Critical | Service down | 4 hours | 2 hours | 1 hour |
| P2 - High | Feature broken | 12 hours | 6 hours | 2 hours |
| P3 - Normal | How-to, question | 24 hours | 12 hours | 4 hours |
| P4 - Low | Feature request | 48 hours | 24 hours | 12 hours |

#### Resolution Time:

**Target (not guaranteed):**
- P1: 24 hours
- P2: 48 hours
- P3: 5 days
- P4: Best effort

---

### Support Ticket Lifecycle:

```
New Ticket
    ↓
Auto-Reply (ticket #, ETA)
    ↓
Assigned to Agent
    ↓
First Response (within SLA)
    ↓
Investigation / Back-and-forth
    ↓
Resolution Proposed
    ↓
Customer Confirms Fixed
    ↓
Ticket Closed
    ↓
Follow-up Survey (24h later)
```

---

### Ticket Categorization:

**Category Tags:**
- `installation` - Setup issues
- `test-creation` - Creating experiments
- `results` - Understanding data
- `billing` - Payment, subscription
- `bug` - Something broken
- `feature-request` - New feature idea
- `integration` - Third-party tools
- `performance` - Speed issues
- `account` - Login, access
- `other` - Miscellaneous

**Use tags to:**
- Prioritize common issues
- Identify product improvements
- Track support burden by area

---

### Canned Responses (Templates):

#### 1. Installation Issue - Not Connecting

```
Hi [Name],

Thanks for reaching out!

I see you're having trouble verifying the installation. Let's 
troubleshoot:

1. Check the snippet is in the <head> section (not <body>)
2. Clear your browser cache and your site's cache
3. Wait 60 seconds and try "Test Installation" again

I checked your account and don't see any data coming through yet. 
Can you:
- Send a screenshot of where you pasted the snippet?
- Send a screenshot of your browser console (F12) when on your site?

This will help me identify the issue quickly.

Best,
[Your name]
```

---

#### 2. Test Not Running

```
Hi [Name],

I see your test "[Test Name]" isn't getting impressions yet.

I checked and the likely issue is: [specific diagnosis]

To fix:
1. [Step 1]
2. [Step 2]

Once done, give it 10-15 minutes and check the dashboard.

If still not working, reply to this email with a screenshot of 
[X] and I'll investigate further.

Best,
[Your name]
```

---

#### 3. Billing Question - Upgrade

```
Hi [Name],

Great to hear you want to upgrade to [Plan]!

Here's what happens:
1. You'll be charged $[amount] today (pro-rated)
2. Your new limits take effect immediately
3. Next billing date: [date]

To upgrade:
Dashboard → Settings → Billing → Upgrade

Or I can do it for you - just reply "yes, upgrade me" and I'll 
process it.

Any questions?

Best,
[Your name]
```

---

#### 4. Feature Request

```
Hi [Name],

Thanks for the suggestion about [feature]!

I've added this to our feature request tracker. We prioritize 
based on:
- Number of requests
- Impact on users
- Technical feasibility

I can't promise when/if we'll build it, but customer feedback 
directly influences our roadmap.

In the meantime, here's a workaround: [if applicable]

I'll update you if we decide to build this!

Best,
[Your name]
```

---

#### 5. Cancellation Request

```
Hi [Name],

Sorry to see you go!

Before I process the cancellation, I'd love to understand:
- What wasn't working for you?
- Was there anything we could have done differently?

Your feedback helps us improve for other customers.

If you're sure about canceling:
- You can cancel yourself: Dashboard → Settings → Cancel
- Or I can do it for you (just reply "yes, cancel")

Your access continues until [end date].
Your data is kept for 30 days if you change your mind.

Thanks for trying Samplit!

Best,
[Your name]
```

---

## 🚨 CHURN PREVENTION

### Early Warning Signals:

**At-Risk Customer = Any of these:**
- ❌ No login in 7+ days (trial users)
- ❌ No login in 14+ days (paid users)
- ❌ No active tests
- ❌ Test created but never launched
- ❌ Support tickets > 3 in one week
- ❌ Downgrade from paid to free
- ❌ Clicked "Cancel subscription" (didn't complete)

**Action:** Proactive outreach

---

### Churn Prevention Playbook:

#### Trigger: No Login in 7 Days (Trial)

**Email:**
```
Subject: Need help with Samplit?

Hi [Name],

I noticed you haven't logged into Samplit in a week.

Common reasons:
- Installation issues?
- Not sure what to test first?
- Too busy to set up?

I'd love to help! Reply to this email and I'll:
- Jump on a quick call to help you set up
- Answer any questions
- Share what successful customers test first

Your trial has [X] days left - let's make them count!

Best,
[Your name]
Founder, Samplit
```

---

#### Trigger: Test Created but Not Launched

**Email:**
```
Subject: Your test is ready to launch

Hi [Name],

I see you created "[Test Name]" but haven't launched it yet.

Stuck on something?

Common blockers:
- Not sure how to define conversion goal?
- Confused by the setup?
- Waiting for something?

I can help! Just reply and I'll guide you through.

Or if you don't need this test anymore, you can delete it 
and start fresh.

Best,
[Your name]
```

---

#### Trigger: Trial Ending (3 Days Left)

**Email:**
```
Subject: 3 days left in your trial

Hi [Name],

Your Samplit trial ends in 3 days.

So far you've:
- Created [X] tests
- Processed [Y] visitors
- [Achievement or result if any]

To continue using Samplit:
[Upgrade to Starter - $29/mo]

Questions about plans? Reply to this email.

Not ready to commit? That's okay - your data is saved for 30 
days if you change your mind.

Best,
[Your name]
```

---

#### Trigger: Paid User - No Login 14 Days

**Email:**
```
Subject: We miss you!

Hi [Name],

Haven't seen you in Samplit for 2 weeks.

Everything okay?

Common reasons customers go quiet:
- Busy season (totally get it!)
- Testing paused (that's fine)
- Issue with the product (let's fix it!)
- Forgot about subscription (want to pause?)

If you're not using Samplit anymore, I'd love to:
1. Understand why (helps us improve)
2. Help you cancel to stop charges

Or if you're just busy and plan to resume testing, that's 
great! Your account will be here when you're ready.

Best,
[Your name]
```

---

#### Trigger: Support Ticket Frenzy (3+ in One Week)

**Internal Alert:** Flag to CSM

**Action:**
1. Review all tickets
2. Identify root cause
3. Proactive call/email offering help
4. Consider discount/extension if product issue

---

#### Trigger: Customer Clicks "Cancel" (Doesn't Complete)

**Email (1 Hour Later):**
```
Subject: Can I help?

Hi [Name],

I noticed you started to cancel your subscription but didn't 
complete it.

If something's not working right, I'd love to fix it!

Common reasons people cancel:
- Price is too high → Let's chat about a discount
- Not using it → We can pause your subscription
- Missing features → Tell me what you need
- Technical issues → I'll fix it personally

Reply to this email or book a quick call:
[Calendar link]

If you definitely want to cancel, that's okay too. Your 
feedback helps us improve.

Best,
[Your name]
```

---

### Cancellation Flow:

When customer cancels:

**Step 1: Exit Survey (Required)**
```
Before you go, help us improve:

Why are you canceling? (Select all that apply)
[ ] Too expensive
[ ] Not using it enough
[ ] Missing features I need
[ ] Too difficult to use
[ ] Found a better alternative
[ ] Technical issues
[ ] Other: _________

What could have kept you as a customer?
[Text box]

[Submit & Cancel]
```

**Step 2: Save Offer (50% of cancellations)**
```
We'd hate to see you go!

Special offer just for you:
- 50% off for 3 months
- OR pause subscription (resume anytime)
- OR downgrade to Free plan

[Accept Offer] [No Thanks, Cancel]
```

**Step 3: Confirm Cancellation**
```
Subscription canceled.

Your access continues until: [End Date]
Your data saved for: 30 days

Changed your mind?
You can reactivate anytime within 30 days without 
losing data.

We'd love to have you back!

[Reactivate Account]
```

**Step 4: Follow-up (7 Days Later)**
```
Hi [Name],

Quick follow-up on your cancellation.

Your data is still saved (23 days left).

If circumstances changed or we've added what you 
needed, you can reactivate with one click:

[Reactivate Account]

Otherwise, no worries! Thanks for trying Samplit.

Best,
[Your name]
```

---

## 📊 CUSTOMER HEALTH SCORING

### Health Score Formula:

```
Health Score (0-100) =
  + Login frequency (30 points)
  + Active tests (25 points)
  + Tests completed (20 points)
  + Support satisfaction (15 points)
  + Payment status (10 points)
```

### Scoring Details:

**Login Frequency (30 pts):**
- 30: Daily
- 20: 2-3x/week
- 10: Weekly
- 5: Biweekly
- 0: < Monthly

**Active Tests (25 pts):**
- 25: 3+ active tests
- 15: 2 active tests
- 10: 1 active test
- 0: 0 active tests

**Tests Completed (20 pts):**
- 20: 5+ completed
- 15: 3-4 completed
- 10: 1-2 completed
- 0: 0 completed

**Support Satisfaction (15 pts):**
- 15: NPS 9-10
- 10: NPS 7-8
- 5: NPS 0-6
- 0: No interaction

**Payment Status (10 pts):**
- 10: Paid, current
- 5: Trial, engaged
- 0: Payment failed / Past due

---

### Health Score Actions:

| Score | Status | Action |
|-------|--------|--------|
| 80-100 | 🟢 Healthy | Upsell, testimonial request |
| 60-79 | 🟡 At Risk | Check-in, offer help |
| 40-59 | 🟠 Unhealthy | Urgent intervention |
| 0-39 | 🔴 Critical | Save or graceful exit |

---

## 💬 CUSTOMER COMMUNICATION

### Communication Cadence:

#### Trial Users:
- Day 0: Welcome email
- Day 1: Installation guide
- Day 2: First test guide
- Day 4: Results guide
- Day 7: Progress check-in
- Day 11: Trial ending reminder (3 days)
- Day 14: Trial ended

#### Paid Users:
- Week 1: Onboarding sequence
- Monthly: Newsletter
- As needed: Feature announcements
- As needed: Support responses

**Don't over-communicate.** Quality > quantity.

---

### Newsletter (Monthly):

**Content:**
- Product updates
- Your tests this month (personal stats)
- Blog post highlights
- Tips & tricks
- Customer spotlight

**Template:**
```
Hi [Name],

Your Samplit monthly update:

📊 YOUR STATS
- Tests run: [X]
- Improvement: +[Y]%
- Time saved: [Z] days

🚀 NEW FEATURES
- [Feature 1]
- [Feature 2]

📝 FROM THE BLOG
- [Post 1]
- [Post 2]

💡 TIP OF THE MONTH
[Quick tip]

See you next month!
[Your name]
```

---

## 🎓 CUSTOMER EDUCATION

### Webinars (Quarterly):

**Topics:**
- "Getting Started with A/B Testing"
- "Advanced Test Strategies"
- "Case Study: How [Customer] Increased Conversions 40%"
- "Q&A with Founders"

**Format:**
- 30-45 minutes
- Live Q&A
- Recording sent to all

---

### Video Tutorials:

**Must-have videos:**
1. "What is Samplit?" (2 min)
2. "Install in 5 Minutes" (5 min)
3. "Create Your First Test" (8 min)
4. "Understanding Results" (6 min)
5. "What to Test First" (10 min)

**Host:** YouTube + embed in docs

---

### Blog (Educational):

**Publish:**
- 2-4 posts/month
- Mix of: How-tos, Case studies, Data insights
- SEO optimized
- Actionable takeaways

[See: blog-writing-guide.md]

---

## 📈 CUSTOMER SUCCESS METRICS

### Track Monthly:

**Activation:**
- % who install tracker (Day 1)
- % who create test (Day 3)
- % who launch test (Day 7)
- Time to first value (average)

**Engagement:**
- % active users (logged in last 30 days)
- Average tests per customer
- Average logins per week

**Retention:**
- Month-over-month retention
- Cohort retention (by signup month)
- Churn rate

**Satisfaction:**
- NPS score
- Support ticket CSAT
- Review scores (G2, Capterra)

**Revenue:**
- Trial → Paid conversion %
- Upgrade rate (Free → Paid)
- Expansion MRR (upgrades)
- Contraction MRR (downgrades)

---

### Goal Setting:

**Year 1 Targets:**
- Activation (Day 7): 40%
- Trial → Paid: 20%
- Churn: <8%
- NPS: >30

**Year 2 Targets:**
- Activation (Day 7): 60%
- Trial → Paid: 30%
- Churn: <5%
- NPS: >50

---

## 🏆 CUSTOMER ADVOCACY

### Building Advocates:

**Identify advocates:**
- Health Score >80
- NPS 9-10
- Using for 3+ months
- Achieved clear results

**Requests:**

**Testimonial:**
```
Hi [Name],

Love seeing the results you're getting with Samplit!

Would you be open to sharing a testimonial?

Just 2-3 sentences about:
- What you tested
- Results you achieved
- Why you like Samplit

We'd feature it on our website (with your permission).

Want to help? Just reply!

Best,
[Your name]
```

**Case Study:**
```
Hi [Name],

Your success with Samplit is impressive:
- [Result 1]
- [Result 2]

Would you be interested in a detailed case study?

What's in it for you:
- Showcase your expertise
- Backlink to your site
- We promote it to our audience

It's a 30-min interview + we write it.

Interested? Let me know!

Best,
[Your name]
```

**Review:**
```
Hi [Name],

Quick favor?

If you're happy with Samplit, would you leave a review 
on [G2/Capterra]?

Takes 2 minutes and really helps us reach more people.

Link: [Review URL]

Thanks!
[Your name]
```

---

## 🎁 CUSTOMER DELIGHT

### Surprise & Delight Moments:

**Customer Milestone:**
```
Email: "Congrats on your 10th test!"

Include:
- Personalized stats
- Badge/achievement graphic
- Discount code for upgrade (if applicable)
```

**Big Win:**
```
When customer gets significant result (>20% improvement):

Email: "Amazing result! 🎉"

Offer:
- Feature in case study?
- Share on social media? (with permission)
- Free month as celebration
```

**Anniversary:**
```
Email: "Happy 1-year with Samplit!"

Include:
- Year in review (personal stats)
- Thank you note
- Small gift (discount, swag, etc.)
```

---

## 🔄 CONTINUOUS IMPROVEMENT

### Feedback Loop:

**Collect:**
- Support ticket trends
- Exit surveys
- NPS feedback
- Feature requests

**Analyze:**
- What's breaking most?
- What's missing most?
- What's confusing most?

**Act:**
- Fix bugs
- Build features
- Improve docs
- Update onboarding

**Communicate:**
- "You asked, we built: [Feature]"
- Show you listen to customers

---

### Customer Advisory Board:

**Select 5-10 top customers:**
- Quarterly calls
- Roadmap input
- Beta access
- Insider insights

**Benefits:**
- Better product decisions
- Stronger customer relationships
- Advocacy boost

---

## ✅ CUSTOMER SUCCESS CHECKLIST

### Launch Day:
- [ ] Help Center live
- [ ] Onboarding emails set up
- [ ] Support email working
- [ ] Canned responses ready
- [ ] SLA defined
- [ ] Health scoring implemented

### First Month:
- [ ] Track activation rate
- [ ] Monitor support volume
- [ ] Collect first NPS scores
- [ ] Identify friction points

### Ongoing:
- [ ] Weekly: Review at-risk customers
- [ ] Monthly: Health score audit
- [ ] Quarterly: Update docs
- [ ] Annually: Survey all customers

---

**Remember:** Customer success isn't a department, it's a philosophy. Every interaction matters.
