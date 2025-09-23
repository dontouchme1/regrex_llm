# regrex_llm
LLM-powered regex matcher and replacer with a Django API and a Vite/React UI.

## Prerequisites
- Python 3.13
- Node.js 18+
- Ollama installed locally (with a model pulled)

## Backend (Django API)
```bash
cd backend
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt

# Optional: set model in backend/.env
# OLLAMA_MODEL=llama3.2

# Run API server
../venv/bin/python manage.py runserver 0.0.0.0:8000 
```

## Frontend (Vite + React)
```bash
cd frontend
npm install
npm run dev 
```

Open the frontend URL shown in the terminal (typically `http://localhost:5173`).


## Demo
<video src="[./asset/demo.gif](https://github.com/dontouchme1/regrex_llm/blob/main/asset/demo.gif)"> </video>
