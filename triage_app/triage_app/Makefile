PY ?= python
export PYTHONPATH := src

.PHONY: install train test app api docker
install:
	$(PY) -m pip install -r requirements.txt
train:            ## (re)build the .pkl artifacts in artifacts/
	$(PY) -m triage_matching.train
test:
	$(PY) -m pytest -q
app:
	streamlit run app/streamlit_app.py
api:
	uvicorn api.main:app --reload
docker:
	docker build -t care-triage . && docker run -p 8501:8501 care-triage
