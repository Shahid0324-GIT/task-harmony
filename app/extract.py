import os
import json
import time
from dotenv import load_dotenv
from groq import Groq
from tqdm import tqdm
from app.schemas import EmailExtractionOutput, ShipmentDetails
from app.prompts import SYSTEM_PROMPT_FINAL, get_user_prompt
import sys
import os

from lib.helper import BASE_DIR

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
EMAIL_PATH = os.path.join(BASE_DIR, "data", "emails_input.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "result", "output.json")


def get_client():
    if not API_KEY:
        print("Warning: GROQ_API_KEY not found. Please set it in .env file.")
        return None
    return Groq(api_key=API_KEY)

def extract_email_data(client, email_id, subject, body, retries=3):
    if not client:
        return None

    prompt = get_user_prompt(subject, body)
    
    for attempt in range(retries):
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_FINAL},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            content = completion.choices[0].message.content
            
            # Basic cleanup if the model returns markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            data = json.loads(content)
            
            # Validate with Pydantic
            shipment = ShipmentDetails(**data)
            
            # Construct final output with ID
            result = EmailExtractionOutput(id=email_id, **shipment.model_dump())
            return result.model_dump()
            
        except Exception as e:
            wait_time = 2 ** attempt
            # print(f"Error processing {email_id} (Attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(wait_time)
            else:
                print(f"Failed to process {email_id} after {retries} attempts: {e}")
                # Return null structure as per requirements
                return {
                    "id": email_id,
                    "product_line": None,
                    "origin_port_code": None,
                    "origin_port_name": None,
                    "destination_port_code": None,
                    "destination_port_name": None,
                    "incoterm": None,
                    "cargo_weight_kg": None,
                    "cargo_cbm": None,
                    "is_dangerous": False
                }

def main():
    client = get_client()
    if not client:
        return

    try:
        with open(EMAIL_PATH, 'r') as f:
            emails = json.load(f)
    except FileNotFoundError:
        print("Error: emails_input.json not found.")
        return

    results = []
    print(f"Processing {len(emails)} emails...")
    
    # Process emails
    for email in tqdm(emails):
        result = extract_email_data(client, email['id'], email['subject'], email['body'])
        if result:
            results.append(result)
        
        # Rate limiting helper (Groq free tier)
        time.sleep(1) 
        
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Extraction complete. Results saved to output.json")

if __name__ == "__main__":
    main()
