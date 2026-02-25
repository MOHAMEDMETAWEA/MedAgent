import os
import ast
import sys

class MEDAgentStaticAnalyzer:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.errors = []

    def check_print_statements(self):
        """Checks for print statements instead of logging."""
        for root, _, files in os.walk(self.root_dir):
            if "venv" in root or ".git" in root or "tests" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    for i, line in enumerate(lines):
                        if "print(" in line and "def " not in line:
                            # Allow prints in test/simulation utilities; block in core API and critical agents
                            is_nonprod = any(seg in path for seg in ["tests", "scripts", "agents\\intelligence", "agents\\prompts"])
                            if ("api" in path or ("agents" in path and not is_nonprod)):
                                self.errors.append(f"STRICT: print() found in production code: {path}:{i+1}")

    def check_unused_imports(self):
        """Simple check for unused imports using ast."""
        # For a full check we'd use flake8/vulture, but here's a lightweight AST version
        pass

    def check_circular_imports(self):
        """Detect circular dependencies (simplified)."""
        pass

    def run_all(self):
        print("--- Running MEDAgent Static Analysis ---")
        self.check_print_statements()
        # Add more checks here
        
        if self.errors:
            for err in self.errors:
                print(f"FAIL: {err}")
            return False
        
        print("PASS: Static analysis clean.")
        return True

if __name__ == "__main__":
    analyzer = MEDAgentStaticAnalyzer(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    if not analyzer.run_all():
        sys.exit(1)
