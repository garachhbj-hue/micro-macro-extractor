# 🔬 Entity Extractor — Micro & Macro NER

A Streamlit app for **Named Entity Recognition (NER)** that classifies entities into:

- **Macro Entities** — high-level semantic: `PERSON`, `ORG`, `GPE`, `LOC`, `EVENT`, `WORK_OF_ART`, `LAW`, `NORP`, `FAC`, `PRODUCT`, `LANGUAGE`
- **Micro Entities** — granular numeric/temporal: `DATE`, `TIME`, `MONEY`, `PERCENT`, `QUANTITY`, `ORDINAL`, `CARDINAL`

---

## ✨ Features

- Paste text or upload `.txt` / `.csv` files
- Color-coded inline annotation of extracted entities
- Side-by-side Macro vs. Micro breakdown with frequency counts
- Export results as **CSV**, **JSON**, or **TXT**
- Dark-mode, minimal UI

---

## 🚀 Run Locally

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/entity-extractor.git
cd entity-extractor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

---

## ☁️ Deploy on Streamlit Community Cloud

1. Push this repo to GitHub (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo, branch `main`, and file `app.py`
4. Click **Deploy** — done!

> The `requirements.txt` includes the spaCy model wheel URL, so Streamlit Cloud installs it automatically.

---

## 📁 Project Structure

```
entity-extractor/
├── app.py               # Main Streamlit application
├── requirements.txt     # Python dependencies + spaCy model
├── .streamlit/
│   └── config.toml      # Dark theme config
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| [Streamlit](https://streamlit.io) | UI framework |
| [spaCy](https://spacy.io) | NLP engine |
| `en_core_web_sm` | English NER model |
| pandas | Data export |

---

## 📄 License

MIT
