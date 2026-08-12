"""
The "after" version — YOUR file to complete.

The three functions below implement the config-driven pipeline. Everything else (CLI wiring,
imports) is already done for you. Do not hardcode any path, format string, or
threshold value anywhere in this file — if you find yourself typing a literal
number or file path outside of a default/example, it belongs in the config
file instead.

Run with:
    python src/pipeline.py --config config/pipeline.yaml
"""
import argparse
import csv
import json

import yaml

REQUIRED_KEYS = ["input_path", "input_format", "high_value_threshold", "output_path"]


def load_config(path):
    """Load a YAML config file and validate required keys are present.

    Must raise ValueError naming the specific missing key if REQUIRED_KEYS
    are not all present. Do not let this fail with a bare KeyError later.
    """
    
    with open(path,'r') as file:
        data = yaml.safe_load(file)
        for key in REQUIRED_KEYS:
            if key not in data:
                raise ValueError(f"{key} not present in yaml file")
    return data


def load_transactions(path, fmt):
    """Load transactions from `path`, using `fmt` ("csv" or "json") to decide
    how to parse it — not by sniffing the file extension.

    Must return a list of dicts. Every dict must have at least "amount"
    (str or float) and "is_fraud" (str "True"/"False" or bool).
    Raise ValueError for any fmt other than "csv" or "json".
    """
    if fmt not in ["csv", "json"]:
        raise ValueError(f"Unsupported format: '{fmt}'. Format must be 'csv' or 'json'.")

    with open(path, 'r') as file:
        if fmt == "csv":
            reader = csv.DictReader(file)
            transactions = list(reader)
        elif fmt == "json":
            transactions = json.load(file)
            
    filtered_transactions = [
        {"amount": tx["amount"], "is_fraud": tx["is_fraud"]} 
        for tx in transactions
    ]
    
    return filtered_transactions


def run_pipeline(config):
    """Load data per `config`, compute the same summary fields as
    pipeline_hardcoded.py (n_transactions, total_amount, fraud_rate,
    n_high_value, high_value_threshold), and write them as JSON to
    config["output_path"]. Return the report dict as well.
    """
    rows = load_transactions(config["input_path"],config["input_format"])
    n = len(rows)
    total_amount = sum(float(r["amount"]) for r in rows)
    
    n_fraud = sum(
        1 for r in rows 
        if (isinstance(r["is_fraud"], bool) and r["is_fraud"]) or 
           (isinstance(r["is_fraud"], str) and r["is_fraud"].strip().lower() == "true")
    )
    
    n_high_value = sum(1 for r in rows if float(r["amount"]) > config["high_value_threshold"])

    report = {
        "n_transactions": n,
        "total_amount": round(total_amount, 2),
        "fraud_rate": round(n_fraud / n, 4) if n else 0.0,
        "n_high_value": n_high_value,
        "high_value_threshold": config["high_value_threshold"],
    }

    with open(config["output_path"], "w") as f:
        json.dump(report, f, indent=2)
    return report


def main():
    parser = argparse.ArgumentParser(description="Config-driven fraud transaction summary pipeline")
    parser.add_argument("--config", required=True, help="Path to a YAML config file")
    args = parser.parse_args()

    config = load_config(args.config)
    report = run_pipeline(config)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
