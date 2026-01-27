import json
import os

def load_port_codes():
    try:
        path = 'port_codes_reference.json'
        if not os.path.exists(path):
            return []
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading port codes: {e}")
        return []

PORT_CODES = load_port_codes()
PORT_REFERENCE_STR = json.dumps(PORT_CODES, indent=2)

# Version 1: Basic extraction (Simulated for history)
PROMPT_V1 = """
Extract shipment details from the email.
Return JSON with: product_line, origin_port_code, destination_port_code, incoterm, cargo_weight_kg, cargo_cbm, is_dangerous.
"""

# Version 2: Added Port Codes context
PROMPT_V2 = f"""
Extract shipment details. Use these port codes:
{PORT_REFERENCE_STR}
Rules:
- Default incoterm to FOB.
- Detect dangerous goods.
- Convert lbs to kg.
"""

# Version 3 (Final): Comprehensive System Prompt
SYSTEM_PROMPT_FINAL = f"""
You are a precise data extraction engine for freight forwarding emails.
Your goal is to extract specific shipment details into a JSON format.

### Reference Data
Use ONLY the following ports for code/name mapping. If a port is not in this list, set code and name to null.
{PORT_REFERENCE_STR}

### Extraction Rules

1. **Product Line**:
   - If Destination is in India (starts with 'IN') -> "pl_sea_import_lcl"
   - If Origin is in India (starts with 'IN') -> "pl_sea_export_lcl"
   - Note: All emails are LCL.

2. **Ports**:
   - Identify Origin and Destination ports.
   - Map to the 5-letter UN/LOCODE from the Reference Data.
   - Use the exact "name" from the Reference Data for the matched code.
   - If multiple ports mentioned, use the Origin -> Destination pair. Ignore transshipment ports.

3. **Incoterm**:
   - Valid values: FOB, CIF, CFR, EXW, DDP, DAP, FCA, CPT, CIP, DPU.
   - Normalize to uppercase.
   - Default to "FOB" if not mentioned or ambiguous.

4. **Cargo Details**:
   - **Weight**: Extract in kg. If in lbs, convert (lbs * 0.453592). Round to 2 decimals.
   - **Volume**: Extract in CBM. Round to 2 decimals.
   - If "0", return 0. If missing/TBD, return null.

5. **Dangerous Goods**:
   - Set `is_dangerous: true` if email contains: "DG", "dangerous", "hazardous", "Class" + number, "IMO", "IMDG".
   - Set `is_dangerous: false` if it says "non-hazardous", "non-DG", "not dangerous" or if no mention.

6. **Conflict Resolution**:
   - Body content takes precedence over Subject.
   - If multiple shipments, extract the FIRST one mentioned in the body.

### Output Format
Return ONLY valid JSON matching this structure:
{{
  "product_line": "string or null",
  "origin_port_code": "string or null",
  "origin_port_name": "string or null",
  "destination_port_code": "string or null",
  "destination_port_name": "string or null",
  "incoterm": "string",
  "cargo_weight_kg": float or null,
  "cargo_cbm": float or null,
  "is_dangerous": boolean
}}
"""

def get_user_prompt(subject: str, body: str) -> str:
    return f"""
Subject: {subject}
Body: {body}
"""
