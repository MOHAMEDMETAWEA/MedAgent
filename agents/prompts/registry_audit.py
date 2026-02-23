"""
Audit script for MedAgent Prompt Registry.
Checks for completeness, safety coverage, and role consistency.
"""
from agents.prompts.registry import PROMPT_REGISTRY, PromptEntry
from typing import List, Set

def audit_completeness():
    print("--- MedAgent Prompt Ecosystem Audit ---")
    
    # 1. Check Use-Case Coverage
    required_modules = {"SYS", "MODE", "LOG", "VIS", "GOV", "SPE", "OP", "REG", "ADV"}
    present_modules = {p.split('-')[1] for p in PROMPT_REGISTRY.keys()}
    
    missing_modules = required_modules - present_modules
    if missing_modules:
        print(f"[!] Missing Modules: {missing_modules}")
    else:
        print("[+] All core modules present.")

    # 2. Safety Coverage Check
    safety_count = 0
    for p_id, entry in PROMPT_REGISTRY.items():
        if "clinical-safety" in entry.governance_flags or entry.risk_level in ["high", "emergency"]:
            safety_count += 1
    
    print(f"[+] Safety-Critical Prompts: {safety_count}")
    
    # 3. Emergency Escalation Check
    emergency_prompts = [p for p in PROMPT_REGISTRY.values() if p.risk_level == "emergency"]
    if not emergency_prompts:
        print("[!] WARNING: No emergency/escalation prompts found!")
    else:
        print(f"[+] Emergency Prompts: {len(emergency_prompts)}")

    # 4. Role Consistency
    roles_covered = set()
    for entry in PROMPT_REGISTRY.values():
        roles_covered.update(entry.applicable_role)
    
    print(f"[+] Roles Covered: {roles_covered}")

if __name__ == "__main__":
    audit_completeness()
