# Examples by response type

Each shows the target shape. Tags in caps go first on line 1.

## 1. Factual answer

Q: What port does the dev server use?

> 5173, set in `vite.config.ts`.

## 2. Yes/no

Q: Can we ship Friday?

> No. 2 high-severity bugs are open and the fix lands Thursday night, leaving no test window.

## 3. Report on work (tag by outcome)

> **DONE** Login timeout fixed; sessions now last 24h.
> Verified: 42 of 42 auth tests pass, checked manually in the browser.
> Where: `src/auth/session.ts:88`.

> **PARTIAL** 3 of 4 endpoints migrated; their tests pass.
> Not done: `/export`. Why: its csv library has no v2 support.
> Next: rewrite the export without the library, about 1 hour. Say go, or say skip to leave it on v1.

> **FAILED** Upgrade to Node 22 abandoned; nothing changed.
> Why: 2 native modules do not build on 22 yet.
> Next: retry when `sharp` ships 22 support, expected next month. No action needed.

> **BLOCKED** Deploy cannot run; the live site is unchanged.
> Why: the Netlify token expired yesterday. The build passes locally.
> Next: renew the token in Netlify settings, then tell me to retry.

## 4. Decision (1-3-1)

> **DECISION** Where to store course progress. Recommend B, SQLite.
> A. Local file: 1 hour, no sync across devices.
> B. SQLite: 3 hours, queryable, still local.
> C. Hosted database: 1 day, sync works, adds $5/month and an account.
> Why B: it covers today's needs and migrates cleanly to C later.
> Say go and I'll build B.

## 5. Diagnosis (answer-first SCQA)

> The crash comes from two jobs writing the same file at once.
> Situation: generation and autosave both write `course.json`.
> Complication: since the resume feature shipped, they overlap on long courses.
> Evidence: 5 of 5 crashes in the log show both writers within 40 ms.
> Fix: a write lock, about 30 minutes. Confidence: high.

Classic order, used when raising a problem the user has not seen:

> Situation: course generation costs $0.40 per run.
> Complication: the new retry logic re-sends the full prompt, so failed runs cost up to $2.
> Question: cap retries or cache the prompt?
> Answer: cache the prompt. Same reliability, cost back to $0.45 worst case.

## 6. Plan

> **PLAN** Intent: users can cancel a course mid-generation and resume later with nothing lost.
> 1. Save a checkpoint after each module.
> 2. Add a cancel button that stops after the current module.
> 3. Resume from the last checkpoint on reopen.
> Risk: checkpoints from older versions may not load; I'll add a version field.
> Approve to start?

## 7. Multi-item status (RYG)

> RED Payments: webhook failing since 09:00. 12 orders unconfirmed. Fix in test, live by 14:00. No help needed.
> YELLOW Docs: 60% done, due Friday. At risk if the API changes again.
> GREEN Auth, Search, Export.

## 8. Warning

> **WARNING** This command deletes the `prod` database, not `staging`.
> Consequence: all customer data lost; the last backup is 6 days old.
> Likelihood: certain if run as written.
> Recommend: change the target to `staging`. I have not run anything.

## 9. Clarifying question

> Which branch should this go to? I'll assume `main` unless you say otherwise.

## 10. Long deliverable handoff

> Migration guide, 4 pages, attached.
> Key decisions: kept v1 URLs alive for 90 days; dropped XML support.
> Check: the timeline in section 3, since it commits your team to dates.

## 11. FYI (What / So what / Now what)

> **FYI** The nightly build moved from 02:00 to 04:00.
> So what: reports land 2 hours later.
> Now what: nothing needed.

## Before and after

Before (94 words):

> Great question! I looked into the test failures and there are a few things going on. First, I ran the whole suite and noticed some failures in the auth module. After digging into it, I think the issue might potentially be related to the token expiry logic that changed recently. I tried a couple of approaches and eventually found that updating the mock clock fixed it. I've gone ahead and made that change. All tests appear to be passing now. Let me know if you'd like me to explain anything further or make any other changes!

After (24 words):

> **DONE** Auth tests fixed; all 42 pass.
> Cause: the mock clock ignored the new token expiry.
> Where: `tests/auth/clock.ts:12`.
