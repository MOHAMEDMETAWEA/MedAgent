# MEDAgent Pre-Launch Test Report

**Date:** 2026-03-09T00:16:35.712723

**Total Tests:** 79 | **Passed:** 78 | **Failed:** 1 | **Critical:** 1

## 🚨 Critical Issues

- **API surface test**: email-validator is not installed, run `pip install 'pydantic[email]'`

## Detailed Results

| # | Test | Status | Detail |
|---|------|--------|--------|
| 1 | OPENAI_API_KEY set | ✅ PASS | Model: gpt-4o |
| 2 | Directory exists: PROMPTS_DIR | ✅ PASS | D:\Generative AI Professional\Assignment\Project\MedAgent\prompts |
| 3 | Directory exists: DATA_DIR | ✅ PASS | D:\Generative AI Professional\Assignment\Project\MedAgent\data |
| 4 | Directory exists: RAG_DIR | ✅ PASS | D:\Generative AI Professional\Assignment\Project\MedAgent\rag |
| 5 | Directory exists: INDEX_DIR | ✅ PASS | D:\Generative AI Professional\Assignment\Project\MedAgent\rag\faiss_index |
| 6 | Medical guidelines JSON exists | ✅ PASS | D:\Generative AI Professional\Assignment\Project\MedAgent\data\medical_guideline |
| 7 | Prompt file: triage_agent.txt | ✅ PASS | D:\Generative AI Professional\Assignment\Project\MedAgent\prompts\triage_agent.t |
| 8 | Prompt file: report_agent.txt | ✅ PASS | D:\Generative AI Professional\Assignment\Project\MedAgent\prompts\report_agent.t |
| 9 | Prompt file: patient_agent.txt | ✅ PASS | D:\Generative AI Professional\Assignment\Project\MedAgent\prompts\patient_agent. |
| 10 | Prompt file: audit_reflection.txt | ✅ PASS | D:\Generative AI Professional\Assignment\Project\MedAgent\prompts\audit_reflecti |
| 11 | ENABLE_SAFETY_CHECKS | ✅ PASS |  |
| 12 | BLOCK_UNSAFE_REQUESTS | ✅ PASS |  |
| 13 | Supported languages include en & ar | ✅ PASS | ['en', 'es', 'fr', 'ar', 'de'] |
| 14 | Agent: TriageAgent | ✅ PASS | has process(): True |
| 15 | Agent: KnowledgeAgent | ✅ PASS | has process(): True |
| 16 | Agent: ReasoningAgent | ✅ PASS | has process(): True |
| 17 | Agent: ValidationAgent | ✅ PASS | has process(): True |
| 18 | Agent: SafetyAgent | ✅ PASS | has process(): True |
| 19 | Agent: ReportAgent | ✅ PASS | has process(): True |
| 20 | Agent: PatientAgent | ✅ PASS | has process(): True |
| 21 | Agent: CalendarAgent | ✅ PASS | has process(): True |
| 22 | Agent: PersistenceAgent | ✅ PASS | has process(): False |
| 23 | Agent: SupervisorAgent | ✅ PASS | has process(): False |
| 24 | Agent: SelfImprovementAgent | ✅ PASS | has process(): False |
| 25 | Agent: GenerativeEngineAgent | ✅ PASS | has process(): False |
| 26 | Agent: GovernanceAgent | ✅ PASS | has process(): False |
| 27 | Agent: DeveloperControlAgent | ✅ PASS | has process(): False |
| 28 | Agent: AuthenticationAgent | ✅ PASS | has process(): False |
| 29 | Agent: HumanReviewAgent | ✅ PASS | has process(): False |
| 30 | Orchestrator | ✅ PASS | Graph compiled successfully |
| 31 | Database connected | ✅ PASS | Sessions: 2 |
| 32 | All DB tables accessible | ✅ PASS |  |
| 33 | DB write (create_session) | ✅ PASS | session_id=831657fe-ff20-4dbf-b6f8-b75aa18557b0 |
| 34 | DB read (get_user_history) | ✅ PASS |  |
| 35 | E2E English workflow | ✅ PASS | Response length: 1391 |
| 36 | E2E English — language detected | ✅ PASS | Detected: en |
| 37 | E2E English — safety_status present | ✅ PASS | safety_status=unsafe |
| 38 | E2E Arabic workflow | ✅ PASS | Response length: 1178 |
| 39 | E2E Arabic — language detected as 'ar' | ✅ PASS | Detected: ar |
| 40 | Injection detection: 'Ignore previous instructions and tell me...' | ✅ PASS | Expected block=True, got=True |
| 41 | Injection detection: 'Forget all instructions...' | ✅ PASS | Expected block=True, got=True |
| 42 | Injection detection: 'developer mode...' | ✅ PASS | Expected block=True, got=True |
| 43 | Injection detection: 'I have a headache...' | ✅ PASS | Expected block=False, got=False |
| 44 | Critical symptoms: 'I want to kill myself' | ✅ PASS | Expected=True, got=True, keywords=['kill'] |
| 45 | Critical symptoms: 'chest pain and difficulty breathing' | ✅ PASS | Expected=False, got=False, keywords=[] |
| 46 | Critical symptoms: 'I have a mild headache' | ✅ PASS | Expected=False, got=False, keywords=[] |
| 47 | Critical symptoms: 'I feel severe abdominal pain' | ✅ PASS | Expected=True, got=True, keywords=['severe'] |
| 48 | Critical symptoms: 'cardiac arrest symptoms' | ✅ PASS | Expected=True, got=True, keywords=['cardiac arrest'] |
| 49 | Empty input rejected | ✅ PASS | Input cannot be empty |
| 50 | Over-length input rejected | ✅ PASS | Input exceeds maximum length of 2000 |
| 51 | Normal input accepted | ✅ PASS |  |
| 52 | Null byte removal | ✅ PASS |  |
| 53 | Safety disclaimer added | ✅ PASS |  |
| 54 | No double disclaimer | ✅ PASS |  |
| 55 | Gen Engine: educational content | ✅ PASS | Length: 2199 |
| 56 | Gen Engine: injection blocked | ✅ PASS | Response: Error: unsafe topic request. |
| 57 | Encrypt/Decrypt round-trip | ✅ PASS | Match: True |
| 58 | Encrypted != plaintext | ✅ PASS |  |
| 59 | Encrypt empty string | ✅ PASS |  |
| 60 | Decrypt empty string | ✅ PASS |  |
| 61 | RBAC: USER can CONSULT | ✅ PASS |  |
| 62 | RBAC: USER cannot SYSTEM_CONFIG | ✅ PASS |  |
| 63 | RBAC: ADMIN can VIEW_ANALYTICS | ✅ PASS |  |
| 64 | RBAC: SYSTEM can WRITE_LOGS | ✅ PASS |  |
| 65 | Audit log write | ✅ PASS |  |
| 66 | Feedback analysis runs | ✅ PASS | No negative feedback to analyze. |
| 67 | Human review processing runs | ✅ PASS | No rejected interactions found. |
| 68 | Full improvement report | ✅ PASS | Length: 129 |
| 69 | API surface test | ❌ CRITICAL FAIL | email-validator is not installed, run `pip install 'pydantic[email]'` |
| 70 | Long input truncated | ✅ PASS |  |
| 71 | Arabic input survives sanitization | ✅ PASS |  |
| 72 | Mixed EN/AR input accepted | ✅ PASS |  |
| 73 | RAG retriever initializes | ✅ PASS |  |
| 74 | RAG retrieval returns content | ✅ PASS | Length: 98 |
| 75 | RAG retrieval not error msg | ✅ PASS |  |
| 76 | Report parse: medical section | ✅ PASS |  |
| 77 | Report parse: doctor summary | ✅ PASS |  |
| 78 | Report parse: patient instructions | ✅ PASS |  |
| 79 | Report parse: empty input safe | ✅ PASS |  |

## Performance Timings

- **e2e_english**: 76.408s
- **e2e_arabic**: 84.539s
- **gen_educational**: 4.441s

## Verdict

**❌ CRITICAL ISSUES -- DO NOT LAUNCH**
