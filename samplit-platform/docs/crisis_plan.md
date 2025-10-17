# CRISIS MANAGEMENT PLAN - SAMPLIT

## 🚨 CRISIS TYPES & RESPONSE

### What is a Crisis?

**Definition:** Event that threatens business continuity, reputation, or customer trust.

**Severity Levels:**
- 🟢 **Minor:** Inconvenience, quick fix
- 🟡 **Moderate:** Affects some users, requires attention
- 🟠 **Major:** Affects many users, significant impact
- 🔴 **Critical:** Service down, data breach, legal issue

---

## 📋 CRISIS SCENARIOS

### 1. TECHNICAL CRISES

#### 🔴 CRITICAL: Complete Service Outage

**What:** Samplit.com is down. Nobody can access.

**Immediate Actions (First 30 minutes):**
1. ✅ **Confirm issue** (check monitoring, try to access)
2. ✅ **Post status update** (status page, Twitter)
3. ✅ **Notify team** (if you have one)
4. ✅ **Start investigating** (logs, server status, AWS dashboard)

**Status Page Update:**
```
🔴 INVESTIGATING

We're aware Samplit is currently unavailable. 
Investigating the cause. Updates every 15 minutes.

Last updated: [Time]
```

**Twitter/Social:**
```
⚠️ Samplit is currently down. We're on it.

Status updates: status.samplit.com

We'll have you back up ASAP. Sorry for the disruption.
```

---

**First Hour Actions:**
1. ✅ **Identify root cause**
2. ✅ **Estimate fix time** (under-promise)
3. ✅ **Update status** (every 15-30 min)
4. ✅ **Prepare communication** (what happened, ETA)

**Status Update:**
```
🟡 IDENTIFIED

Issue: [Brief technical explanation in plain English]
Impact: Service unavailable for all users
ETA: Restored within 2 hours

We're working on a fix. Your data is safe.

Last updated: [Time]
```

---

**Recovery Actions:**
1. ✅ **Fix issue**
2. ✅ **Test thoroughly** (don't rush)
3. ✅ **Gradual rollout** (if possible)
4. ✅ **Monitor closely**

**Status Update:**
```
🟢 RESOLVED

Samplit is back online. All services operational.

What happened: [Honest explanation]
Duration: [X hours]
Prevention: [What we're doing to prevent recurrence]

We're sorry for the disruption. Questions? support@samplit.com

Last updated: [Time]
```

---

**Post-Mortem (Within 48h):**

**Blog Post: "Incident Report - [Date]"**

```markdown
# Incident Report: [Date] Outage

## Summary
On [date] at [time], Samplit experienced a complete 
service outage lasting [duration].

## Impact
- All users unable to access dashboard
- Active tests continued running (no data loss)
- [X] customers affected

## Root Cause
[Technical explanation, honest but not too detailed]

## Timeline
- [Time]: Issue detected
- [Time]: Status page updated
- [Time]: Root cause identified
- [Time]: Fix deployed
- [Time]: Service restored

## Resolution
[What we did to fix it]

## Prevention
We're implementing:
1. [Specific measure 1]
2. [Specific measure 2]
3. [Specific measure 3]

## Apology
We're sorry. We know you rely on Samplit. We're 
committed to improving our reliability.

Questions? Email: support@samplit.com

- [Your Name], Founder
```

---

**Customer Compensation (Optional but Recommended):**
```
Email to all affected:

Subject: Our apology + account credit

Hi [name],

You were affected by yesterday's outage. 

I'm sorry. That's not the experience you deserve.

As an apology:
• 1 week free credit added to your account
• Priority support for 30 days
• Direct email to me if you need anything: [your email]

We've implemented [measures] to prevent recurrence.

Thanks for your patience.

[Your name]
```

---

#### 🟠 MAJOR: Partial Service Degradation

**What:** Slow performance, some features broken.

**Response:**
- Status update within 15 minutes
- Fix within 2-4 hours
- Communication: Transparent about impact
- Post-mortem: If affects >10% users

---

#### 🟡 MODERATE: Bug Affecting Some Users

**What:** Specific feature broken for some users.

**Response:**
- Support ticket response
- Status update if widespread (>5% users)
- Fix within 24-48 hours
- Email affected users when fixed

---

### 2. SECURITY CRISES

#### 🔴 CRITICAL: Data Breach

**What:** Unauthorized access to customer data.

**IMMEDIATE ACTIONS (Within 1 hour):**

1. ✅ **Contain breach** 
   - Shut down affected systems
   - Revoke compromised credentials
   - Block attacker access

2. ✅ **Assess scope**
   - What data accessed?
   - How many users affected?
   - When did breach occur?

3. ✅ **Notify authorities** (GDPR requirement)
   - Report to DPA within 72 hours
   - Document everything

4. ✅ **Legal counsel**
   - Call lawyer immediately
   - Follow their guidance

---

**Customer Notification (ASAP, per GDPR):**

**Email:**
```
Subject: Important Security Notice

Dear [name],

I'm writing with difficult news.

On [date], we discovered unauthorized access to 
our systems. We believe your data may have been 
affected.

What happened:
[Honest explanation without technical jargon]

Data potentially affected:
• [List specific data types]
• [What was NOT affected]

What we've done:
• Contained the breach immediately
• Engaged security experts
• Reported to authorities
• Implementing additional security measures

What you should do:
• [Specific actions: change password, etc.]
• Monitor for [specific threats]

We take full responsibility. This is unacceptable.

Free credit monitoring: [If applicable]
Direct support: security@samplit.com

I'm personally overseeing our response.

I'm sorry.

[Your Name]
Founder, Samplit
[Your direct email/phone]
```

---

**Public Statement:**
```
SECURITY INCIDENT NOTIFICATION

On [date], Samplit experienced a security incident.

Impact: [X] users potentially affected
Data: [Types of data]
Status: Contained, investigation ongoing

Actions taken:
• Breach contained within [timeframe]
• Law enforcement notified
• Affected users contacted
• Enhanced security implemented

We deeply regret this incident. Full details:
[Link to detailed post]

Questions: security@samplit.com
```

---

**Long-term Actions:**
- Security audit (third-party)
- Implement recommendations
- Regular penetration testing
- Transparency report (what changed)
- Rebuild trust (takes time)

---

#### 🟡 MODERATE: Security Vulnerability Reported

**What:** Researcher finds vulnerability, reports it.

**Response:**

1. ✅ **Thank researcher**
2. ✅ **Verify vulnerability**
3. ✅ **Patch immediately** (within 24h)
4. ✅ **Disclose responsibly** (coordinate with researcher)
5. ✅ **Credit researcher** (if they want)

**No need for customer panic if:**
- No exploitation occurred
- Fixed before public disclosure
- No data accessed

**Small blog post acknowledging fix is sufficient.**

---

### 3. REPUTATION CRISES

#### 🟠 MAJOR: Negative Viral Post

**What:** Angry customer posts on Twitter/Reddit, goes viral.

**Example:**
```
Twitter: "Samplit charged me €500 instead of €50! 
Customer support ignoring me for 3 days! Scam?? 
@samplit [angry emoji]"

[2000+ retweets, trending]
```

---

**Response (Within 1-2 hours):**

**1. Investigate Immediately**
- Is complaint valid?
- What actually happened?
- Our fault or misunderstanding?

**2. Respond Publicly (Quickly & Honestly)**

**If our fault:**
```
Hi [name], I'm the founder. I'm so sorry this happened.

This is a billing error on our end - completely 
unacceptable. 

I've:
• Refunded you fully
• Added 3 months free
• Personally fixing the bug that caused this

DM me directly if anything else needed.

We screwed up. I'm sorry.
```

**If misunderstanding:**
```
Hi [name], I'm the founder. I see the confusion.

What happened: [Clear explanation]

This isn't a scam - [proof]. But I understand the 
frustration.

DMing you now to make this right.
```

**3. Move to Private**
- DM/Email to resolve fully
- Make it RIGHT (refund, credit, whatever needed)
- Follow up publicly when resolved

**4. Learn & Improve**
- If process issue: fix it
- If communication issue: improve
- Blog post if widely misunderstood

---

**What NOT to do:**
❌ Ignore it (makes it worse)
❌ Delete/block (proves guilt)
❌ Argue publicly (looks defensive)
❌ Blame customer (never)
❌ Hide (transparency wins)

---

#### 🟡 MODERATE: Bad Review (G2, Trustpilot)

**What:** Negative review posted.

**Response:**

**Public Reply:**
```
Hi [Reviewer],

Thanks for the feedback. I'm sorry Samplit didn't 
meet your expectations.

Specific to your points:
• [Address point 1]
• [Address point 2]

We're working on [improvement]. Your feedback helps.

If you're open to discussing further: [email]

- [Your Name], Founder
```

**Private Outreach:**
```
Email subject: Following up on your review

Hi [name],

Saw your review on [platform]. I'm the founder.

First, I'm sorry for [specific issue].

I'd love to understand more about your experience 
and see if there's a way to make it right.

Could we jump on a 15-min call? Or if you prefer, 
just reply here.

No sales pitch - just want to learn and improve.

Best,
[Your name]
```

**Possible outcomes:**
- They update review (great!)
- They stay unhappy but appreciate response
- They ghost (that's ok)

**Key:** Professional, empathetic, action-oriented.

---

### 4. FINANCIAL CRISES

#### 🔴 CRITICAL: Running Out of Cash

**What:** <3 months runway remaining.

**Immediate Actions:**

**1. Get Cash NOW (30 days):**
- Offer annual discount (get 12 months upfront)
- Email existing customers
- Accelerate sales cycle
- Consider small loan (family, friends)
- Credit line (if possible)

**2. Cut Costs IMMEDIATELY:**
- Cancel non-essential services
- Reduce hosting costs
- Pause ads (focus organic)
- Defer own salary (if solo)

**3. Explore Options (60 days):**
- Investor (if open to it)
- Acquirer (if exit makes sense)
- Loan (carefully)
- Co-founder with capital

**4. Communicate (If necessary):**

**To customers (only if closing):**
```
Important update about Samplit's future

[Honest explanation of situation]

Options:
1. If you're annual: Full refund
2. If you're monthly: Service through [date]

Export your data: [link]

I'm sorry I couldn't make this work.

[Your name]
```

---

#### 🟠 MAJOR: Payment Processor Issues

**What:** Stripe account frozen/limited.

**Response:**

**1. Contact Stripe Immediately**
- Understand why
- Provide requested documentation
- Escalate if needed

**2. Alternative Processor (Backup)**
- Have backup ready (PayPal, Paddle)
- Can switch in emergency

**3. Communicate to Customers**
```
Temporary payment issue - not your fault

We're experiencing technical issues with payment 
processing. Your service continues uninterrupted.

If your payment failed:
• Don't worry - not a charge issue on your end
• We're resolving this today
• Your account stays active

Update: [status page]
```

---

### 5. LEGAL CRISES

#### 🔴 CRITICAL: Cease & Desist Letter

**What:** Lawyer letter claiming IP infringement.

**DO NOT Panic. DO:**

1. ✅ **Read carefully**
   - What exactly are they claiming?
   - What do they want (stop using name, feature, etc.)?
   - Deadline?

2. ✅ **DO NOT respond immediately**
   - Do NOT admit anything
   - Do NOT agree to anything
   - Do NOT ignore it

3. ✅ **Get lawyer (ASAP)**
   - IP lawyer
   - Show them letter
   - Follow their advice

4. ✅ **Assess merit**
   - Valid claim?
   - Nuisance suit?
   - Cost to fight vs settle?

**Timeline:**
- Day 1: Receive letter → Get lawyer
- Day 2-5: Lawyer reviews, advises
- Day 5-10: Respond (through lawyer)

**Customer Communication:**
- Usually NOT needed unless affects product
- If name change required: transparent communication

---

#### 🟠 MAJOR: GDPR Complaint

**What:** User files complaint with Data Protection Authority.

**Response:**

1. ✅ **Document everything**
   - What data you have
   - How you got it
   - How you use it
   - Your legal basis

2. ✅ **Respond to DPA**
   - Within their deadline
   - Honest, complete
   - Show compliance efforts

3. ✅ **Fix any issues**
   - If you're wrong: fix it
   - Update processes
   - Document changes

4. ✅ **Legal counsel**
   - GDPR lawyer
   - Especially if complex

---

### 6. PERSONAL CRISES (Founder)

#### 🔴 CRITICAL: Founder Incapacitated

**What:** You're in hospital, can't work for weeks/months.

**Preparation (DO THIS NOW):**

**1. Succession Document**
```
EMERGENCY CONTACT INFORMATION

In case I'm incapacitated:

Primary Contact:
Name: [Person]
Phone: [Number]
Email: [Email]
Relationship: [Family/Friend/Co-founder]

They have access to:
□ This document
□ Password manager (1Password vault)
□ Business bank account
□ Stripe account
□ AWS console
□ Domain registrar

Critical Passwords:
[In password manager shared vault]

Immediate Actions:
1. Post status update: "Samplit experiencing 
   temporary delay. Updates soon."
2. Email customers: "Service continues. Support 
   response may be delayed."
3. Contact: [Lawyer/Accountant] for business decisions

Server Access:
[Emergency access documentation]

Customer Communication:
[Template emails in Google Drive: /emergency]

If prolonged (>1 month):
- Consider temporary shutdown
- Full refunds to annual customers
- Transparent communication

DO NOT just disappear.
```

**2. Share with Trusted Person**
- Family member
- Close friend
- Future co-founder
- Lawyer

**3. Update Quarterly**

---

## 📢 CRISIS COMMUNICATION PRINCIPLES

### Golden Rules:

**1. Speed Matters**
- First response within 1 hour
- Don't wait for perfect information
- "We're aware, investigating" is better than silence

**2. Honesty Wins**
- Admit mistakes
- Don't minimize
- Don't blame others
- Own it

**3. Empathy First**
- Acknowledge impact
- "I'm sorry" is powerful
- Put yourself in their shoes

**4. Be Specific**
- "Some users" → "Approximately 200 users"
- "Soon" → "Within 2 hours"
- "Issue" → "Database connection failure"

**5. Show Action**
- What you're DOING (not just sorry)
- Timeline
- Prevention measures

**6. Multiple Channels**
- Status page
- Twitter/social
- Email (affected users)
- Blog (major issues)

---

### Communication Templates:

#### Status Page Update
```
[Emoji Status] [STATUS LEVEL]

[What's happening in 1 sentence]

Impact: [Who's affected, how]
Cause: [If known]
ETA: [Estimate]

We're [specific action]. Updates every [frequency].

Last updated: [Time] UTC
```

---

#### Twitter Update
```
⚠️ [Brief issue description]

Status: [Status level]
Updates: status.samplit.com

[If major: Apology]
[If resolved: Thanks for patience]
```

---

#### Customer Email (Major Issue)
```
Subject: [Brief description] - We're on it

Hi [name],

Quick update: [Issue description]

Impact on you:
• [Specific impact]
• [What still works]

What we're doing:
• [Action 1]
• [Action 2]

ETA: [Realistic estimate]

Your data is safe. [If applicable]

We're sorry for the disruption.

Updates: status.samplit.com

Questions? Reply to this email.

[Your name]
```

---

## 🛡️ CRISIS PREVENTION

### Monitoring & Alerts

**Set up NOW:**

1. ✅ **Uptime Monitoring**
   - Pingdom, UptimeRobot, or similar
   - Check every 1-5 minutes
   - Alert via: SMS, Email, Slack

2. ✅ **Error Tracking**
   - Sentry, Rollbar, or similar
   - Alert on: Error rate spikes

3. ✅ **Performance Monitoring**
   - New Relic, DataDog, or similar
   - Alert on: Slow response times

4. ✅ **Security Monitoring**
   - Failed login attempts
   - Unusual API usage
   - OWASP top 10

---

### Status Page

**Setup:** status.samplit.com

**Show:**
- Current status (all green = all good)
- Incident history
- Scheduled maintenance
- Subscribe to updates

**Tools:**
- Statuspage.io
- Atlassian Statuspage
- Self-hosted (cachet)

**Update:**
- During incidents: Every 15-30 min
- After resolved: Post-mortem within 48h

---

### Backup & Recovery

**Critical:**

1. ✅ **Database Backups**
   - Automated daily (minimum)
   - Stored off-site
   - Test restore quarterly

2. ✅ **Code Backups**
   - Git (obviously)
   - Private repos
   - Multiple remotes

3. ✅ **Configuration Backups**
   - Infrastructure as Code
   - Documented
   - Version controlled

4. ✅ **Disaster Recovery Plan**
   - How to restore from zero
   - Tested at least once
   - Documented step-by-step

---

### Insurance

**Consider:**

**1. Cyber Liability Insurance**
- Covers: Data breaches, cyber attacks
- Cost: €500-2000/year (depends on size)
- Worth it when: >100 customers

**2. Business Interruption Insurance**
- Covers: Lost revenue from outages
- Cost: Varies
- Worth it when: Significant MRR

**3. Errors & Omissions (E&O)**
- Covers: Professional mistakes
- Cost: €1000-3000/year
- Worth it when: Enterprise customers

**Check with insurance broker for specifics.**

---

## 📋 CRISIS RESPONSE CHECKLIST

### When Crisis Hits:

**Immediate (First hour):**
- [ ] Confirm issue exists
- [ ] Assess severity (🟢🟡🟠🔴)
- [ ] Post initial status update
- [ ] Notify team (if applicable)
- [ ] Start investigating

**Short-term (First 4 hours):**
- [ ] Identify root cause
- [ ] Estimate fix time
- [ ] Update status (every 30 min)
- [ ] Begin resolution
- [ ] Email affected customers (if major)

**Resolution:**
- [ ] Fix issue
- [ ] Test thoroughly
- [ ] Deploy carefully
- [ ] Monitor closely
- [ ] Update status: Resolved

**Post-Crisis (48 hours):**
- [ ] Write post-mortem
- [ ] Publish transparency report
- [ ] Implement prevention measures
- [ ] Thank team/customers
- [ ] Review response (what to improve)

---

## 📞 EMERGENCY CONTACTS

### Keep Updated:

```
EMERGENCY CONTACTS

Infrastructure:
• AWS Support: [Number/Portal]
• Cloudflare: [Support]
• Stripe: [Support email]

Legal:
• Lawyer: [Name, Phone, Email]
• IP Lawyer: [If different]

Financial:
• Bank: [Business account contact]
• Accountant: [Name, Phone]

Insurance:
• Cyber Insurance: [Policy #, Contact]
• Business Insurance: [Policy #, Contact]

Personal:
• Family Emergency Contact: [Name, Phone]
• Backup Founder Access: [Name, Phone]

Vendors:
• Domain Registrar: [Login, Support]
• Email Provider: [Support]
```

**Print this. Keep physical copy.**

---

## 💡 FINAL THOUGHTS

### Remember:

**1. Crises WILL Happen**
Not if, but when. Be prepared.

**2. Speed > Perfect**
Respond fast with incomplete info > wait for perfect response

**3. Honesty Builds Trust**
Own mistakes. Customers forgive honest mistakes.

**4. Learn from Each**
Every crisis = opportunity to improve

**5. You're Not Alone**
Other founders have been through worse. Ask for help.

---

### Mental Health Note:

**Crises are stressful. Take care of yourself:**

- Don't panic (easier said than done)
- Sleep (even when crisis)
- Ask for help (other founders, mentors)
- Therapy if needed (startup therapy is real)
- Remember: This too shall pass

**Your health > business**

---

**Hope you never need this. But if you do, you're prepared.**
