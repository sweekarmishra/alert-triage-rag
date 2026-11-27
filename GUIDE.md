# Complete Guide: LLM-Powered Security Alert Triage Assistant (RAG)

Everything you need to run it, test it, put it on GitHub, host it on Render, put it on your resume and demo it.

---

## 1. What you built (30-second version)

An alert comes in ("412 failed SSH logins in 5 minutes..."). The system:

1. **Retrieves** the most relevant runbook sections with TF-IDF.
2. **Prompts** an LLM with only those sections and asks for JSON: attack type, severity, summary, recommended actions with citations.
3. **Validates** the answer: valid JSON, allowed values, and every citation must be a runbook section that was actually retrieved.
4. **Falls back** to a rule-based triage if the LLM fails (bad JSON, invented citation, API error). Offline mode uses only the rules.

```
alert -> TF-IDF retrieve -> prompt -> LLM -> validate --ok--> result
                                         \-- fail / error --> rule-based fallback --> result
```

Files:

| Path | Purpose |
|---|---|
| `triage/retriever.py` | Splits runbooks into sections, TF-IDF + cosine similarity |
| `triage/prompt.py` | Prompt and JSON schema |
| `triage/validator.py` | JSON parsing, schema checks, citation grounding check |
| `triage/fallback.py` | Rule-based classifier, severity, runbook-derived actions |
| `triage/llm.py` | LLM client interface, Anthropic Messages API client |
| `triage/pipeline.py` | The end-to-end flow above |
| `server.py`, `static/index.html` | Flask API and the interactive GUI |
| `tests/test_triage.py` | The 11 pytest tests (mocked LLM) |
| `data/runbooks/` | 9 runbooks, 26 sections |
| `data/alerts.json` | 18 labeled alerts: 13 attacks, 5 benign |

---

## 2. Run it locally

**Linux / macOS**
```bash
cd alert-triage-rag
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest -q          # expect: 11 passed
python3 server.py             # open http://127.0.0.1:5055
```

**Windows (PowerShell)**
```powershell
cd alert-triage-rag
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python server.py
```

GUI tips: click an alert, press **Run triage** (or Enter), use the arrow keys to move through alerts, toggle **ground truth**, hover a citation to highlight its source text, open the **Evaluation** tab and run it to see 13/13.

---

## 3. Test the live LLM path (needs your own API key)

This was **not** tested against the real API in the session that built it (no key available there). It was tested against a local stub that mimics the API: success, HTTP 500, malformed response and refused connection all behaved correctly. Do the real test once yourself:

```bash
export ANTHROPIC_API_KEY=sk-ant-...        # Windows: $env:ANTHROPIC_API_KEY="sk-ant-..."
# optional: export TRIAGE_MODEL=claude-haiku-5-5
python3 server.py
```

Then in the GUI pick **Live API** and run a few alerts. Check:
- Pipeline log says `validate: schema ok...` and the badge shows **LLM · validated**: the real model worked.
- If you see **rule-based fallback** with an error, read the red message. Common causes: wrong key, no credit, a model name your account cannot use (set `TRIAGE_MODEL`), or the model citing a section it was not shown. All of these are handled by design.

Do not paste your key into any file that is committed to GitHub.

---

## 4. Put it on GitHub

The project folder is already a git repository with one commit. You only need to create an empty repo and push.

1. On github.com click **New repository**. Name: `alert-triage-rag`. Leave it **empty** (no README, no .gitignore, no license). Public is best for a portfolio.
2. In the project folder:
```bash
git config user.name "Your Name"
git config user.email "your-github-email@example.com"
git commit --amend --reset-author --no-edit      # makes the commit yours
git remote add origin https://github.com/<your-username>/alert-triage-rag.git
git push -u origin main
```
3. If asked to log in, use a **personal access token** as the password (GitHub > Settings > Developer settings > Tokens), or run `gh auth login` first.
4. On the repo page: add the description *"RAG assistant that turns anomaly alerts into grounded, validated incident summaries"* and topics `rag`, `llm`, `security`, `tf-idf`, `pytest`, `flask`.
5. Add a screenshot: run the app, take a screenshot, save it as `docs/screenshot.png`, add `![GUI](docs/screenshot.png)` near the top of `README.md`, commit and push.

---

## 5. Host it on Render (free)

The repo already contains `render.yaml`, `gunicorn` in `requirements.txt`, and the server reads Render's `PORT`.

**Option A: Blueprint (easiest)**
1. Push to GitHub first (section 4).
2. Render dashboard > **New** > **Blueprint** > connect GitHub > pick `alert-triage-rag` > **Apply**.

**Option B: manual**
1. Render > **New** > **Web Service** > pick the repo.
2. Runtime **Python 3**, Build command `pip install -r requirements.txt`, Start command `gunicorn server:app --bind 0.0.0.0:$PORT --workers 1 --timeout 60`, Instance type **Free**.
3. Environment: `PYTHON_VERSION` = `3.12.7`.

After deploy, open `https://<your-service>.onrender.com`. Check `/api/meta` returns JSON and the GUI loads.

Things to know:
- **Free tier sleeps** after about 15 minutes idle. The first visit after that takes 30 to 60 seconds. Open it yourself a minute before showing anyone.
- **Live API on a public URL spends your money.** Safest choice: do *not* set `ANTHROPIC_API_KEY` on Render. The site then runs offline mode and the fault-injection simulations, which already demonstrate everything. If you do add the key, there is a built-in limit of 10 live calls per hour per visitor (`LIVE_LIMIT_PER_HOUR`).
- `gunicorn` could not be installed in the build session, so the exact Render start command is untested there. If Render's log shows an error, paste it and fix from there; the app itself is verified.

Put the live URL in the GitHub repo's "Website" field and in your resume.

---

## 6. Resume text (exactly as you sent it)

**LLM-Powered Security Alert Triage Assistant (RAG)**

- Built a retrieval-augmented assistant that turns anomaly alerts into structured incident summaries (attack type, severity, recommended actions) grounded in security runbooks, using TF-IDF retrieval and an LLM prompt that returns JSON.
- Added output validation, including a check that every citation comes from the retrieved runbook text, and a rule-based fallback when the LLM fails; the offline mode identified the correct attack type for 13 of 13 true attacks.
- Wrote 11 pytest tests with a mocked LLM client covering invalid JSON, invented citations and API errors.

Every claim maps to the code: TF-IDF in `retriever.py`, JSON prompt in `prompt.py`, citation check in `validator.py`, fallback in `fallback.py`, 13/13 in `test_11` and the Evaluation tab, and exactly 11 tests in `tests/test_triage.py`. Do not add more tests without updating the resume number.

---

## 7. Demo script for your GL / TL (5 minutes)

1. **Problem (30 s):** "Analysts get alerts with raw numbers. This turns each into a summary plus actions taken from our own runbooks, and it never invents sources."
2. **Happy path (60 s):** pick ALR-001, mode *LLM · valid output*, Run. Point at the pipeline lighting up, the retrieved sections ranked by score, and hover a citation to show it highlights the exact runbook text.
3. **Trust (90 s):** switch to *LLM · invented citation*, Run. Show the red rejection and the amber fallback. Then *invalid JSON* and *API error*. Message: the system degrades safely instead of showing bad output.
4. **Offline and numbers (60 s):** Evaluation tab, Run. 13/13 true attacks, benign alerts left alone.
5. **Custom alert (30 s):** paste a new alert text, show it classifies live.
6. **Telecom link (30 s):** "Same pattern applies to core network logs: retrieval over procedures, validated output, deterministic fallback."

---

## 8. Interview questions you should expect

**Why TF-IDF and not embeddings?**
Small, specialized, keyword-heavy corpus (runbooks full of terms like SYN, UNION SELECT). TF-IDF is fast, needs no model download, is deterministic and easy to debug. Embeddings would be the next step if the runbooks grew or used varied wording.

**How do you stop the LLM from hallucinating?**
Two layers. The prompt restricts it to the retrieved excerpts, and the validator rejects any citation that is not a retrieved section id, then falls back to rules. It checks citations, not the truth of every sentence; say that honestly.

**Is 13/13 meaningful?**
It shows the offline rules and the pipeline work on 13 labeled scenarios. The alerts are synthetic and I labeled them, and the rules were written against the same style, so it is not a claim about real-world accuracy. With real alerts I would expect lower and would measure precision and recall per class.

**What happens when the LLM is down?**
The pipeline catches API errors, timeouts, bad JSON and failed validation and returns the rule-based result, marked as `fallback` with the reason.

**Why mock the LLM in tests?**
Deterministic, free, fast, and it lets me force the exact failure modes (invalid JSON, invented citation, API error).

**What would you improve?**
Real alert data, per-class metrics, embedding or hybrid retrieval, validating that action text is supported by the cited section, severity calibration, and logging for analyst feedback.

**How does this relate to your C-DOT work?**
Both are validation problems: define expected behavior, check outputs against it, and have a safe path when something is wrong. Test automation and fault injection are the same habits.

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: sklearn` | `pip install -r requirements.txt` inside the venv |
| GUI blank / 404 | Run `python3 server.py` from the project folder |
| Port 5055 busy | `PORT=5080 python3 server.py` (this also binds 0.0.0.0) |
| Live API always falls back | Read the red error in the result card; check key, credit, `TRIAGE_MODEL` |
| Render build fails | Open the build log; confirm Python 3.12 and that `requirements.txt` is at repo root |
| Render page slow first time | Free tier waking up, wait up to a minute |
| `git push` rejected | The GitHub repo was not empty; create a fresh empty one |

---

## 10. Checklist

- [ ] `pytest` shows 11 passed on your machine
- [ ] Live API tested once with your key (optional but recommended before claiming it)
- [ ] Commit author fixed, pushed to GitHub, screenshot added
- [ ] Deployed on Render, URL works, put in repo Website field
- [ ] Resume text unchanged, GitHub and demo links added
- [ ] Practiced the 5-minute demo and the interview answers above
