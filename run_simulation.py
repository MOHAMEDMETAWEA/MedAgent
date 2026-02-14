from agents.orchestrator import MedAgentOrchestrator
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

def run_emergency_simulation():
    print("="*60)
    print("🏥 MEDAGENT EMERGENCY ROOM SIMULATION")
    print("="*60)
    
    # 🚨 Scenario: Patient with classic "Red Flag" symptoms of a heart attack
    emergency_symptoms = (
        "I am a 55-year-old male. For the last 20 minutes, I've had a crushing pain in the middle of my chest. "
        "It feels like an elephant is sitting on me. The pain is traveling up to my left jaw and down my left arm. "
        "I'm also feeling very sweaty, nauseous, and I'm having trouble catching my breath."
    )
    
    print(f"\n[PATIENT INTAKE]: {emergency_symptoms}\n")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not found in .env file.")
        print("Please add your key to run this live simulation.")
        return

    try:
        orchestrator = MedAgentOrchestrator()
        
        print("🔄 Agents are collaborating... (Step-by-Step logs will appear below)")
        result = orchestrator.run(emergency_symptoms)
        
        print("\n" + "-"*40)
        print("✅ SIMULATION COMPLETE")
        print("-"*40)
        
        print(f"\n🤖 [AGENT 1: PATIENT SUMMARY]:\n{result.get('patient_info', {}).get('summary')}")
        
        print(f"\n🧠 [AGENT 2: AI CLINICAL DIAGNOSIS & REASONING]:\n{result.get('preliminary_diagnosis')}")
        
        print(f"\n📅 [AGENT 3: RESOURCE ALLOCATION & SCHEDULING]:")
        alert_status = "🚨 EMERGENCY 🚨" if result.get('critical_alert') else "NORMAL"
        print(f"STATUS: {alert_status}")
        print(result.get('appointment_details'))
        
        print(f"\n🩺 [AGENT 4: DOCTOR'S FINAL VALIDATION]:\n{result.get('doctor_notes')}")
        
        if result.get('report_medical') or result.get('report_doctor_summary') or result.get('report_patient_instructions'):
            print(f"\n📝 [AGENT 5: GENERATIVE REPORT (RAG)]:")
            if result.get('report_medical'):
                print(f"  تقرير طبي / Medical Report:\n{result.get('report_medical')}")
            if result.get('report_doctor_summary'):
                print(f"  Summary للطبيب:\n{result.get('report_doctor_summary')}")
            if result.get('report_patient_instructions'):
                print(f"  تعليمات للمريض:\n{result.get('report_patient_instructions')}")
        
    except Exception as e:
        print(f"\n❌ SIMULATION FAILED: {str(e)}")

if __name__ == "__main__":
    run_emergency_simulation()
