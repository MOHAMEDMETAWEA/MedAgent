import os
import re
import sys

class MEDAgentSecurityScanner:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.vulnerabilities = []
        # Patterns for secrets
        self.secret_patterns = [
            r"sk-[a-zA-Z0-9]{48}", # OpenAI
            r"AIza[0-9A-Za-z\\-_]{35}", # Google API
            r"['\"][0-9a-fA-F]{32}['\"]", # Symmetric keys
        ]

    def scan_secrets(self):
        print("[1] Scanning for hardcoded secrets...")
        for root, _, files in os.walk(self.root_dir):
            if any(x in root for x in ["venv", ".git", "medagent.db"]): continue
            for file in files:
                if file.endswith((".py", ".env", ".txt")):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for pattern in self.secret_patterns:
                            if re.search(pattern, content):
                                if ".env.example" in path: continue
                                self.vulnerabilities.append(f"CRITICAL: Potential secret leaked in {path}")

    def scan_sqli(self):
        print("[2] Checking for SQL injection patterns...")
        # Check for f-strings in execute() calls
        for root, _, files in os.walk(self.root_dir):
            if "database" not in root: continue
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if ".execute(f\"" in line or ".execute(\"" + "{" in line:
                                self.vulnerabilities.append(f"HIGH: Potential SQLi vulnerable query at {path}:{i+1}")

    def run_all(self):
        print("--- Running MEDAgent Security Validation ---")
        self.scan_secrets()
        self.scan_sqli()
        
        if self.vulnerabilities:
            for v in self.vulnerabilities:
                print(f"FAIL: {v}")
            return False
        
        print("PASS: No immediate security vulnerabilities detected.")
        return True

if __name__ == "__main__":
    scanner = MEDAgentSecurityScanner(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    if not scanner.run_all():
        sys.exit(1)
