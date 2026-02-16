# 🚀 How to Run MedAgent (User Guide)

Follow these steps to run the MedAgent medical consultation system on your machine.

---

## What You Need

- **Python 3.9 or newer** ([python.org](https://www.python.org/downloads/))
- **OpenAI API key** ([platform.openai.com](https://platform.openai.com/api-keys)) — required for the AI to work
- A terminal (Command Prompt, PowerShell, or Terminal app)

---

## Step 1: Open the project folder in a terminal

- **Windows:** Open the folder in File Explorer, type `cmd` in the address bar and press Enter, or right‑click the folder → “Open in Terminal”.
- **Mac/Linux:** Open Terminal and run: `cd /path/to/DepiGraduationProject_MedAgent...` (use your actual project path).

All commands below must be run from this **project root** folder (where you see `requirements.txt`, `config.py`, and the `api` folder).

---

## Step 2: Create a virtual environment (recommended)

**Windows (Command Prompt or PowerShell):**

```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in the prompt. Then use `pip` and `python` as in the next steps.

---

## Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

Wait until installation finishes without errors.

---

## Step 4: Set your OpenAI API key

1. Copy the example env file into a file named `.env`:

   **Windows (Command Prompt):**

   ```bash
   copy .env.example .env
   ```

   **Windows (PowerShell) or Mac/Linux:**

   ```bash
   cp .env.example .env
   ```

2. Open the `.env` file in a text editor and replace `your_api_key_here` with your real OpenAI API key:

   ```bash
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

   Save and close the file. **Do not share this file or commit it to Git.**

---

## Step 5: Generate medical data (first time only)

This creates the medical guidelines used by the system:

```bash
python data/generate_data.py
```

You should see: `Generated ... medical_guidelines.json` and `Generated ... patient_registry.csv`.

---

## Step 6: Start the System

### Method A: The Easy Way (Recommended)

Run the unified launcher script. This will start both the backend and the frontend for you.

```bash
python run_system.py
```

- Backend API: **<http://localhost:8000>**
- Frontend UI: **<http://localhost:8501>** (opens automatically)

### Method B: The Manual Way

If you prefer to run them separately (e.g., for troubleshooting), follow these steps:

1. **Start the Backend:**

   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```

2. **Start the Frontend (New Terminal):**

   ```bash
   streamlit run api/frontend.py --server.port 8501
   ```

Your browser should open to **<http://localhost:8501>**.

---

## Step 8: Use the app

1. In the web page, type your symptoms in the text box (e.g. “I have a headache and fever”).
2. Click **Start Consultation**.
3. Wait a few seconds. You will see:
   - Patient intake summary  
   - Preliminary AI differential  
   - Next steps / appointment guidance  
   - Clinical note (SOAP-style)

**Disclaimer:** This is for educational and informational use only. It is not a substitute for professional medical advice. In an emergency, contact your local emergency services.

---

## Troubleshooting

| Problem | What to do |
| :--- | :--- |
| **“OPENAI_API_KEY Missing”** | Create `.env` from `.env.example` and set `OPENAI_API_KEY=your_key`. Restart the backend. |
| **“No module named …”** | Run `pip install -r requirements.txt` from the project root. |
| **Port 8000 already in use** | Stop the program using port 8000, or use another port: `uvicorn api.main:app --port 8001`. Then set in `.env`: `MEDAGENT_API_URL=http://localhost:8001` and use that port in the frontend. |
| **Port 8501 already in use** | Use another port: `streamlit run api/frontend.py --server.port 8502` and open <http://localhost:8502>. |
| **Frontend says “API Offline”** | Start the backend first (Step 6). Ensure it is running on <http://localhost:8000>. |
| **“medical_guidelines.json not found”** | Run Step 5: `python data/generate_data.py`. |

---

## Optional: Run with Docker

If you have Docker and Docker Compose installed:

```bash
cd deployment
docker-compose up -d
```

Backend: <http://localhost:8000>  
Frontend: <http://localhost:8501>  

Put your `.env` (with `OPENAI_API_KEY`) in the **parent** of the `deployment` folder (project root).

---

## Summary checklist

- [ ] Python 3.9+ installed  
- [ ] In project root: `pip install -r requirements.txt`  
- [ ] `.env` created from `.env.example` with your `OPENAI_API_KEY`  
- [ ] `python data/generate_data.py` run once  
- [ ] Terminal 1: `uvicorn api.main:app --host 0.0.0.0 --port 8000`  
- [ ] Terminal 2: `streamlit run api/frontend.py --server.port 8501`  
- [ ] Browser: <http://localhost:8501>  

For deployment and security details, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.
