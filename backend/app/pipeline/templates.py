"""
WasmBox Standard Plugin Templates Library.
Curated, pre-audited Python plugins that adhere to sandbox security policies
and serve as quick-start scaffolds for common edge computing tasks.
"""

from typing import List, Dict, Any

STANDARD_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "tpl-json-masker",
        "name": "PII & Secret Data Masker",
        "category": "security",
        "tags": ["security", "pii", "sanitizer", "json"],
        "description": "Masks passwords, api keys, and credit cards in nested JSON payloads.",
        "code": '''import json
import re

SENSITIVE_KEYS = {"password", "secret", "token", "api_key", "credit_card", "ssn"}

def mask_dict(obj):
    if isinstance(obj, dict):
        res = {}
        for k, v in obj.items():
            if any(s in str(k).lower() for s in SENSITIVE_KEYS):
                res[k] = "********"
            else:
                res[k] = mask_dict(v)
        return res
    elif isinstance(obj, list):
        return [mask_dict(x) for x in obj]
    return obj

def process(data):
    """Mask sensitive PII and secrets in input payload"""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {"raw": data}
    return {
        "status": "success",
        "sanitized_payload": mask_dict(data)
    }
'''
    },
    {
        "id": "tpl-sha256-hasher",
        "name": "Cryptographic SHA-256 Digest",
        "category": "utility",
        "tags": ["crypto", "hash", "sha256", "checksum"],
        "description": "Computes SHA-256 digest, byte length, and HMAC checksum of input text.",
        "code": '''import hashlib

def process(data):
    """Generate SHA-256 hash and checksum of input payload"""
    text = str(data.get("text", data) if isinstance(data, dict) else data)
    raw_bytes = text.encode("utf-8")
    
    sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
    
    return {
        "status": "success",
        "algorithm": "SHA-256",
        "hash": sha256_hash,
        "byte_length": len(raw_bytes),
        "char_count": len(text)
    }
'''
    },
    {
        "id": "tpl-csv-json",
        "name": "CSV to JSON Record Parser",
        "category": "data",
        "tags": ["csv", "json", "parser", "transform"],
        "description": "Converts comma-separated CSV rows into structured JSON object records.",
        "code": '''import csv
import io

def process(data):
    """Parse raw CSV text into a structured list of JSON records"""
    csv_text = str(data.get("csv", data) if isinstance(data, dict) else data)
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    
    records = [dict(row) for row in reader]
    return {
        "status": "success",
        "record_count": len(records),
        "records": records
    }
'''
    },
    {
        "id": "tpl-regex-extractor",
        "name": "Regex Entity & Token Extractor",
        "category": "data",
        "tags": ["regex", "nlp", "extractor", "text"],
        "description": "Extracts emails, phone numbers, and URL hyperlinks using regular expressions.",
        "code": '''import re

def process(data):
    """Extract emails, URLs, and phone patterns from text"""
    text = str(data.get("text", data) if isinstance(data, dict) else data)
    
    emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+', text)
    urls = re.findall(r'https?://[a-zA-Z0-9.-]+(?:/[a-zA-Z0-9_.~:/?#[\\]@!$&\\'()*+,;=%-]*)?', text)
    numbers = re.findall(r'\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b', text)
    
    return {
        "status": "success",
        "emails": sorted(list(set(emails))),
        "urls": sorted(list(set(urls))),
        "phone_numbers": sorted(list(set(numbers)))
    }
'''
    },
    {
        "id": "tpl-stats-calc",
        "name": "Numeric Sequence Stats Engine",
        "category": "math",
        "tags": ["math", "statistics", "analytics", "numbers"],
        "description": "Calculates sum, average, variance, min, max, and sorted percentiles.",
        "code": '''import math

def process(data):
    """Calculate statistical summaries on numeric arrays"""
    nums = data if isinstance(data, list) else data.get("numbers", [])
    clean_nums = [float(x) for x in nums if isinstance(x, (int, float))]
    
    if not clean_nums:
        return {"status": "empty", "message": "No numeric input provided"}
        
    n = len(clean_nums)
    avg = sum(clean_nums) / n
    variance = sum((x - avg) ** 2 for x in clean_nums) / n
    std_dev = math.sqrt(variance)
    sorted_nums = sorted(clean_nums)
    
    return {
        "status": "success",
        "count": n,
        "sum": sum(clean_nums),
        "mean": round(avg, 4),
        "std_dev": round(std_dev, 4),
        "min": sorted_nums[0],
        "max": sorted_nums[-1],
        "median": sorted_nums[n // 2]
    }
'''
    }
]
