# Backend / AI Engineer Assessment - Submission

**Candidate:** Mohammed Jameel Shahid
**Submission Date:** 2026-01-28

---

## Overview

This repository contains the solution for the Task Harmony Backend/AI Engineer Assessment. The system extracts structured shipment details from freight forwarding emails using the Groq API (Llama 3.3 70B).

**Key Features:**

- **High Accuracy:** Achieved **91.78%** overall accuracy on the provided dataset.
- **Robust Extraction:** Handles complex business rules, including India detection, incoterm defaults, and dangerous goods identification.
- **Scalable Design:** Built with Pydantic for validation and modular Python scripts.

---

## Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone <repo-url>
   cd <repo-name>
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   - Copy `.env.example` to `.env`
   - Add your Groq API key:

     ```
     GROQ_API_KEY=your_key_here
     ```

4. **Run Extraction:**

   ```bash
   python -m app.extract
   ```

   _Processes `emails_input.json` and generates `output.json`._

5. **Evaluate Accuracy:**

   ```bash
   python -m app.evaluate
   ```

   _Compares `output.json` against `ground_truth.json`._

---

## Prompt Evolution

I followed an iterative approach to refine the prompts, moving from basic extraction to a rule-heavy system prompt.

### v1: Basic Extraction

- **Approach:** Simple prompt asking for JSON output with the required fields.
- **Performance:** ~60% accuracy.
- **Issues:**
  - Hallucinated port codes (e.g., "CN SHA" instead of "CNSHA").
  - Missed default incoterms (null instead of "FOB").
  - Failed to convert units (lbs to kg).

### v2: Context-Aware

- **Approach:** Injected the full `port_codes_reference.json` into the prompt context. Added basic instructions for unit conversion.
- **Performance:** ~80% accuracy.
- **Issues:**
  - **India Detection:** Struggled to assign `pl_sea_import_lcl` vs `pl_sea_export_lcl` correctly based on port codes.
  - **Ambiguity:** Sometimes picked the wrong port if multiple were mentioned (e.g., transshipment ports).

### v3: Business Logic Integration (Final)

- **Approach:**
  - Explicit "System Prompt" defining the persona.
  - Hardcoded business rules: "If Destination starts with 'IN' -> Import".
  - Strict conflict resolution: "Body wins over Subject".
  - Dangerous goods keyword lists.
- **Performance:** **91.78%** accuracy.
- **Remaining Issues:**
  - Minor port name mismatches (e.g., "Chennai" vs "Chennai ICD") due to multiple mappings for the same code in the reference file.

---

## Accuracy Metrics

Results from `evaluate.py`:

| Field                     | Accuracy   | Correct/Total |
| ------------------------- | ---------- | ------------- |
| **product_line**          | 96.00%     | 48/50         |
| **origin_port_code**      | 98.00%     | 49/50         |
| **origin_port_name**      | 92.00%     | 46/50         |
| **destination_port_code** | 96.00%     | 48/50         |
| **destination_port_name** | 64.00%     | 32/50         |
| **incoterm**              | 96.00%     | 48/50         |
| **cargo_weight_kg**       | 90.00%     | 45/50         |
| **cargo_cbm**             | 94.00%     | 47/50         |
| **is_dangerous**          | 100.00%    | 50/50         |
| **OVERALL ACCURACY**      | **91.78%** | **413/450**   |

**Note on Port Names:** The lower accuracy for `destination_port_name` (64%) is largely due to the reference file containing multiple names for the same code (e.g., `INMAA` -> "Chennai" and "Chennai ICD"). The model often picked the valid but "wrong" variant according to the strict ground truth. The `port_code` accuracy (96%) confirms the correct location was identified.

---

## Edge Cases Handled

1. **Dangerous Goods Negation**
   - **Issue:** Emails containing "Non-hazardous" were initially flagged as dangerous because they contained the word "hazardous".
   - **Solution:** Added explicit negative lookahead rules in the prompt: _Set `is_dangerous: false` if it says "non-hazardous", "non-DG"._
   - **Example:** `EMAIL_006` correctly identified as safe.

2. **Subject vs. Body Conflict**
   - **Issue:** Subject says "FOB" but Body says "CIF".
   - **Solution:** Added a "Conflict Resolution" section to the prompt explicitly stating "Body content takes precedence".
   - **Example:** Correctly extracted incoterms when discrepancies existed.

3. **Implicit Port Names**
   - **Issue:** Emails mentioning "Japan" instead of a specific port city.
   - **Solution:** The reference list includes `{"code": "JPUKB", "name": "Japan"}`. The prompt was instructed to match against the provided list names exactly.
   - **Result:** `EMAIL_011` was a tricky case where the model sometimes missed the generic "Japan" mapping, but overall coverage for specific ports was high.

---

## System Design Questions

### 1. Scale: 10,000 emails/day

**Architecture:**
To handle 10,000 emails/day (~7 emails/minute) with a 5-minute SLA, I would use an event-driven architecture:

- **Ingestion:** Emails are pushed to a queue (e.g., AWS SQS or RabbitMQ).
- **Processing:** A scalable worker pool (AWS Lambda or ECS containers) pulls messages.
- **LLM Layer:**
  - Use a high-throughput provider (Groq is excellent here).
  - Implement a fallback strategy (e.g., if Groq fails, failover to OpenAI gpt-4o-mini).
  - Caching: Hash email bodies to avoid re-processing duplicates.
- **Storage:** Store results in a relational DB (PostgreSQL) for structured querying.

**Budget ($500/mo):**

- 10k emails \* 30 days = 300k emails/month.
- Input tokens: ~500/email -> 150M tokens. Output: ~100/email -> 30M tokens.
- **Groq:** Currently free/cheap for Llama 3.
- **OpenAI (gpt-4o-mini):** ~$0.15/1M in, $0.60/1M out. Total ~ $22 (Input) + $18 (Output) = $40/month.
- The budget is easily met, leaving room for infrastructure costs.

### 2. Monitoring

**Detection:**

- **Null Rate Monitoring:** Alert if `product_line` or `port_code` null rate exceeds 10% in a moving 1-hour window.
- **Distribution Checks:** Monitor the ratio of `is_dangerous` (should be stable ~10-20%). If it spikes to 80%, the prompt might be broken.
- **Golden Set:** Run a synthetic "canary" dataset of 50 known emails every hour to verify pipeline integrity.

**Investigation:**

- **Log Analysis:** Check raw LLM responses for refusal patterns or formatting errors.
- **Traceability:** Store the `prompt_version` and `model_version` with every record.
- **Feedback Loop:** Build a UI for operations teams to manually correct entries; use these corrections to fine-tune the prompt or few-shot examples.

### 3. Multilingual Support

**Changes:**

- **Prompting:** Update the system prompt: _"You are a multilingual extraction engine. Translate non-English text to English internally before extracting details."_ Llama 3 and GPT-4 handle this natively.
- **Language Detection:** Add a `language` field to the output schema for analytics.

**Evaluation:**

- **Test Set:** Create a specific test set for Mandarin and Hindi (50 emails each).
- **Native Review:** Have native speakers verify the ground truth for these emails.
- **Metrics:** Track accuracy per language bucket. If Hindi accuracy lags, add Hindi-specific few-shot examples to the prompt.
