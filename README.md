# 🧹 Data Cleaning Automation Tool

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0F2027,50:203A43,100:2C5364&height=180&section=header&text=DATA%20CLEANING%20SYSTEM&fontSize=38&fontColor=ffffff&fontAlignY=40&desc=Clean%20%7C%20Validate%20%7C%20Analyze%20%7C%20Export&descAlignY=62&descSize=17" width="100%" alt="Animated Data Cleaning System header" />

<img src="https://readme-typing-svg.demolab.com/?font=Fira+Code&weight=600&size=21&duration=2500&pause=900&color=00C9FF&center=true&vCenter=true&width=850&height=45&lines=Automated+Data+Cleaning;Python+%7C+Pandas+%7C+Streamlit;Data+Profiling+%26+Quality+Scoring;Smart+Validation+%26+Reporting;AI-Assisted+Cleaning+Recommendations" alt="Typing animation" />

**An end-to-end data-quality platform for profiling, cleaning, validating, analyzing, and exporting real-world datasets.**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

</div>

---

## 🚀 Overview

The **Data Cleaning Automation Tool** turns messy CSV/Excel datasets into cleaner, validated and report-ready data through a guided pipeline:

```text
Upload → Profile → Detect Problems → Select Rules → Clean
        → Validate → Score Quality → Compare → Export
```

It supports both **Simple Mode** for quick one-click cleaning and **Advanced Mode** for users who need column-level control, custom rules, validation, database input, AI recommendations, and large-file processing. fileciteturn25file0L2-L2

> 🎯 **Design principle:** potentially destructive issues are surfaced for review instead of being silently removed.

---

## ✨ Key Features

### 🧹 Automated Cleaning

- Trim extra spaces
- Remove exact duplicates
- Standardize text and capitalization
- Convert text-based numbers into numeric values
- Currency-aware number conversion
- Parse and standardize dates
- Fill missing values using configurable strategies

### 🔍 Data Profiling

- Column data types
- Missing-value analysis
- Unique-value health checks
- Dataset-level quality overview

### 🧠 Smart Issue Detection

- Missing values
- Exact and fuzzy duplicates
- Text inconsistencies
- Invalid dates
- Type mismatches
- Outliers using IQR, Z-score and percentile methods

### 📊 Quality & Validation

- Completeness
- Accuracy
- Consistency
- Uniqueness
- Validity
- Overall **Data Quality Score**
- Business-rule validation
- Before/After comparison

### 🤖 AI-Assisted Recommendations

AI recommendations analyze the **data profile rather than sending the raw dataset** and suggest which existing deterministic cleaning modules should be used. The actual cleaning remains controlled by the application's data-processing pipeline. fileciteturn25file0L2-L2

### 📈 Interactive Dashboard

- Missing-values charts
- Column-type visualization
- Numeric correlation heatmap
- Quality-score gauge
- Per-metric progress indicators
- Interactive cleaning controls

### 🗄️ Database & Large File Support

- SQLite and PostgreSQL through SQLAlchemy-compatible connections
- Load database tables as working datasets
- Write cleaned results back to a table
- Chunked processing for large CSV files
- Memory-conscious streaming workflow

### 📝 Audit & Export

- Timestamped cleaning log
- Transformation history
- Export cleaned data as CSV/Excel
- Export reports as Excel/PDF

---

## ⚡ Simple Mode vs Advanced Mode

| Mode | Best For | Capabilities |
|---|---|---|
| ✨ Simple | Beginners & quick cleaning | Upload → detect → one-click clean → quality score → export |
| 🛠️ Advanced | Analysts & power users | Column-level rules, validation, AI suggestions, database & large-file workflows |

---

## 🏗️ Processing Architecture

```text
                  ┌──────────────────┐
                  │   CSV / Excel /  │
                  │     Database     │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │  Data Profiling  │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Problem Detection│
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Cleaning Rules   │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Clean + Validate │
                  └────────┬─────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              Quality Score   Audit Log
                    │             │
                    └──────┬──────┘
                           ▼
                  ┌──────────────────┐
                  │ Excel / CSV / PDF│
                  └──────────────────┘
```

---

## 🧰 Tech Stack

| Layer | Technologies |
|---|---|
| Language | Python |
| Data Processing | Pandas |
| Application UI | Streamlit |
| Visualization | Plotly |
| Database | SQLite, PostgreSQL, SQLAlchemy |
| AI Recommendations | Anthropic API integration |
| Export | CSV, Excel, PDF |

---

## 📂 Project Structure

```text
Data-Cleaning-System-v3/
├── app.py
├── modules/
│   ├── file_handler.py
│   ├── profiling.py
│   ├── missing_values.py
│   ├── duplicates.py
│   ├── text_cleaning.py
│   ├── standardization.py
│   ├── type_conversion.py
│   ├── date_cleaning.py
│   ├── outlier_detection.py
│   ├── validation.py
│   ├── report.py
│   ├── db_handler.py
│   ├── ai_recommendations.py
│   ├── large_file_handler.py
│   ├── rules_manager.py
│   └── auto_clean.py
├── utils/
│   ├── logger.py
│   └── helpers.py
├── config/
│   └── cleaning_rules.json
├── data/
│   ├── input/
│   └── output/
└── requirements.txt
```

The repository currently contains dedicated modules for profiling, cleaning, validation, reporting, database handling, AI recommendations, large-file processing, custom rules and one-click cleaning. fileciteturn25file0L2-L2

---

## 🛡️ Data Safety Philosophy

This project follows a **user-in-control** approach:

- Outliers are flagged instead of silently deleted.
- Fuzzy duplicates can be reviewed before applying changes.
- Standardization suggestions can be accepted or ignored.
- Cleaning actions are recorded in an audit log.
- AI suggestions route through deterministic cleaning functions rather than directly modifying the dataset.

---

## ⚙️ Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Anand99-master/Data-Clening-System-verson3.git
cd Data-Clening-System-verson3
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal, usually:

```text
http://localhost:8501
```

### 🔐 Optional AI Configuration

If AI recommendations are enabled, configure the required API key through the application's sidebar or environment configuration. **Never commit real API keys to GitHub.**

---

## 🎯 Use Cases

- Preparing raw business datasets for analysis
- Cleaning Excel/CSV files before dashboard creation
- Data-quality assessment
- Preprocessing datasets for machine learning
- Detecting inconsistent values and invalid records
- Validating business rules
- Producing auditable cleaning reports

---

## 🚧 Future Improvements

- Advanced duplicate detection for chunked datasets
- Parallel processing for very large files
- Phonetic matching such as Soundex
- Multi-user authentication
- Additional data-quality rules

---

## 👨‍💻 Author

**Anand Sharma**  
Data Analyst | Data Science Enthusiast | Python | SQL | Power BI

⭐ If this project is useful, consider starring the repository.

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00C9FF,50:203A43,100:0F2027&height=90&section=footer" width="100%" alt="Animated footer" />

**🧹 Clean • Validate • Analyze • Improve 🚀**

</div>
