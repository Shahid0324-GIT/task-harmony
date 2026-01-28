import json
import sys
import os

from lib.helper import BASE_DIR

OUTPUT_PATH = os.path.join(BASE_DIR, "result", "output.json")
GROUND_TRUTH_PATH = os.path.join(BASE_DIR, "data", "ground_truth.json")

def normalize_string(s):
    if s is None:
        return None
    return str(s).strip().upper()

def compare_floats(f1, f2):
    if f1 is None and f2 is None:
        return True
    if f1 is None or f2 is None:
        return False
    # Round to 2 decimal places for comparison
    return round(float(f1), 2) == round(float(f2), 2)

def compare_values(field, val1, val2):
    if field in ['cargo_weight_kg', 'cargo_cbm']:
        return compare_floats(val1, val2)
    if field == 'is_dangerous':
        # Boolean comparison
        return val1 == val2
    # String comparison
    return normalize_string(val1) == normalize_string(val2)

def main():
    try:
        with open(OUTPUT_PATH, 'r') as f:
            predictions = json.load(f)
        with open(GROUND_TRUTH_PATH, 'r') as f:
            ground_truth = json.load(f)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        print("Make sure both output.json and ground_truth.json exist.")
        return

    # Create a map for easy lookup
    gt_map = {item['id']: item for item in ground_truth}
    
    fields_to_evaluate = [
        'product_line',
        'origin_port_code',
        'origin_port_name',
        'destination_port_code',
        'destination_port_name',
        'incoterm',
        'cargo_weight_kg',
        'cargo_cbm',
        'is_dangerous'
    ]
    
    correct_counts = {field: 0 for field in fields_to_evaluate}
    total_counts = {field: 0 for field in fields_to_evaluate}
    
    total_correct_fields = 0
    total_fields = 0
    mismatches = []
    
    for pred in predictions:
        email_id = pred['id']
        if email_id not in gt_map:
            print(f"Warning: ID {email_id} not found in ground truth.")
            continue
            
        gt = gt_map[email_id]
        
        for field in fields_to_evaluate:
            pred_val = pred.get(field)
            gt_val = gt.get(field)
            
            is_correct = compare_values(field, pred_val, gt_val)
            
            total_counts[field] += 1
            total_fields += 1
            
            if is_correct:
                correct_counts[field] += 1
                total_correct_fields += 1
            else:
                mismatches.append(f"Mismatch {email_id} [{field}]: Pred={pred_val}, GT={gt_val}")

    print("\n--- Evaluation Results ---\n")
    print(f"{'Field':<25} | {'Accuracy':<10} | {'Correct/Total'}")
    print("-" * 55)
    
    for field in fields_to_evaluate:
        correct = correct_counts[field]
        total = total_counts[field]
        accuracy = (correct / total * 100) if total > 0 else 0
        print(f"{field:<25} | {accuracy:6.2f}%   | {correct}/{total}")
        
    overall_accuracy = (total_correct_fields / total_fields * 100) if total_fields > 0 else 0
    print("-" * 55)
    print(f"{'OVERALL ACCURACY':<25} | {overall_accuracy:6.2f}%   | {total_correct_fields}/{total_fields}")

if __name__ == "__main__":
    main()
