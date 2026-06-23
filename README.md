---
title: Leaderboard
colorFrom: yellow
emoji: 🏆
colorTo: gray
sdk: streamlit
sdk_version: "1.51.0"
app_file: app.py
pinned: true
short_description: Data science/ML notebook leaderboard
---

# Notebook Leaderboard

[![Unit Tests](https://github.com/gperdrizet/leaderboard/actions/workflows/test.yml/badge.svg)](https://github.com/gperdrizet/leaderboard/actions/workflows/test.yml) [![HF Spaces Deployment](https://github.com/gperdrizet/leaderboard/actions/workflows/deploy-to-hf.yml/badge.svg)](https://github.com/gperdrizet/leaderboard/actions/workflows/deploy-to-hf.yml)

A Kaggle-style leaderboard application for Jupyter notebook submissions, built with Streamlit and designed to run on HuggingFace Spaces.

The currently deployed instance is scoring a feature engineering activity notebook for AI/ML & data science boot camp students:

1. Leaderboard on [HuggingFace spaces](https://huggingface.co/spaces/gperdrizet/leaderboard)
2. Template [submission notebook](https://github.com/gperdrizet/FSA_devops/blob/main/notebooks/unit2/lesson_16/Lesson_16_activity.ipynb)


## Table of Contents

1. [Features](#features)
2. [Using the leaderboard](#using-the-leaderboard)
3. [Running the leaderboard locally (development set-up)](#running-the-leaderboard-locally-development-set-up)
4. [Deployment to HuggingFace Spaces](#deployment-to-huggingface-spaces)
5. [Project Structure](#project-structure)
6. [Contributing](#contributing)
7. [License](#license)


## 1. Features

- **Upload Notebooks**: Students can upload Jupyter notebooks through a web interface
- **Automatic Execution**: Notebooks are executed automatically in a sandboxed environment
- **Scoring System**: Outputs are evaluated and scored based on customizable criteria
- **Live Leaderboard**: Public leaderboard showing rankings in real-time
- **User Statistics**: Track individual submission history and performance
- **Validation**: Built-in validation for file format, size, and structure

## 2. Using the leaderboard

1. **Prepare your notebook**
   - Ensure all cells run without errors
   - Follow the assignment requirements
   - Test locally before submitting

2. **Submit your notebook**
   - Go to the "Home & Submit" page
   - Enter your username (3-50 characters)
   - Upload your `.ipynb` file
   - Click "Submit"

3. **Check your results**
   - View your score and rank immediately after submission
   - Check the leaderboard to see your standing
   - View your submission history in "My Stats"


## 3. Running the leaderboard locally (development set-up)

1. **Clone or download this repository**

2. **Create and activate a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Run the application**

```bash
streamlit run app.py
```

5. **Run the tests**

```bash
python3 -m unittest discover tests -v
```

6. **Open your browser** to `http://localhost:8501`


### 3.1. Customizing the Scoring Function

The scoring logic is in `src/scorer.py`. Customize the `score_notebook()` method to match your assignment requirements:

```python
def score_notebook(self, executed_notebook_path: str, output_data: Optional[Dict] = None) -> Tuple[float, str]:
    # Add your custom scoring logic here
    score = 0.0
    feedback = "Your feedback here"
    return score, feedback
```


### 3.2. Admin Panel

The application includes a PIN-protected admin panel for managing submissions.

**Setup**: Set the `ADMIN_PIN` Space Secret (see deployment steps below). For local development, set it as an environment variable:

```bash
export ADMIN_PIN=your_secure_pin
```

**Access**: Navigate to the "Admin" page in the sidebar and enter your PIN.

**Features**:
- View all submissions with ID, username, score, status, and timestamp
- Remove individual submissions by ID with automatic leaderboard recalculation
- Secure PIN-based authentication (session-based)


### 3.3. Execution Timeout

Default timeout is 5 minutes. Change it in `app.py`:

```python
st.session_state.notebook_runner = NotebookRunner("data/outputs", timeout_seconds=300)
```


### 3.4. File Size Limit

Default max file size is 10MB. Change it in `utils/validation.py`:

```python
validator = NotebookValidator(max_file_size_mb=10.0)
```


### 3.5. Maintenance Utilities

Three CLI utilities are available for database maintenance. All use the `Database` class and will sync changes to the Hub dataset repo automatically if `HF_TOKEN` and `HF_DB_REPO` are set.

```bash
# List all submissions and remove one by ID
python utils/remove_submission.py
python utils/remove_submission.py <id>

# Mark stuck 'running' submissions as 'failed'
python utils/clean_running_submissions.py

# Re-execute and re-score all notebooks in data/submissions/
python utils/reprocess_submissions.py
```

## 4. Deployment to HuggingFace Spaces

Deploying requires three HuggingFace resources: a **Space** (hosts the app), a **dataset repository** (persists the database across restarts), and an **access token** (lets the app read and write the dataset repo). Once the token and two configuration values are added as Space Secrets, the app is fully self-contained - the database is pulled from the dataset repo on every startup and pushed back after every write, so no data is lost when the Space restarts or redeploys.

### 4.1. Create a HuggingFace Space

Go to [huggingface.co/spaces](https://huggingface.co/spaces) → **New Space**.
- SDK: **Streamlit**
- Visibility: Public (or Private)


### 4.2. Create a database dataset repository

The submission database is persisted in a separate HuggingFace dataset repo so it survives redeployments.

Go to [huggingface.co/new-dataset](https://huggingface.co/new-dataset):
- Set visibility to **Private**
- Note the repo ID (e.g. `your-username/leaderboard-db`)


### 4.3. Create an access token

Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → **Create new token**:
- Type: **Fine-grained**
- Grant **Write** access to both the Space repo and the dataset repo


### 4.4. Add Space Secrets

In your Space → **Settings → Variables and secrets**, add:

| Secret | Value |
|---|---|
| `HF_TOKEN` | The token from step 3 |
| `HF_DB_REPO` | Dataset repo ID, e.g. `your-username/leaderboard-db` |
| `ADMIN_PIN` | A secure PIN for the admin panel (6+ characters) |


### 4.5. CI/CD (GitHub actions)

Two workflows handle CI/CD automatically:

- **Unit Tests** (`.github/workflows/test.yml`) - runs on every pull request to `main`. A PR must pass tests before it can be merged.
- **HF Spaces Deployment** (`.github/workflows/deploy-to-hf.yml`) - runs automatically on every push to `main` (i.e. after a PR is merged) and pushes the latest code to the HuggingFace Space.

To enable deployment, add the access token from step 3 as a GitHub repository secret named `LEADERBOARD_GITHUB_DEPLOYMENT` (**Settings → Secrets and variables → Actions → New repository secret**).


### 4.6. Deploy

Open a pull request against `main`. Once the unit tests pass and the PR is merged, the deployment workflow triggers automatically and the Space is updated. On first startup the app creates a fresh database and pushes it to the dataset repo. All subsequent restarts pull the latest database from the dataset repo automatically.


## 5. Project Structure

```
.
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .streamlit/
│   └── config.toml           # Streamlit configuration
├── src/
│   ├── __init__.py
│   ├── database.py           # SQLite database operations + Hub sync
│   ├── notebook_runner.py    # Notebook execution engine
│   ├── scorer.py             # Scoring logic
│   ├── leaderboard.py        # Leaderboard management
│   └── logger.py             # Logging configuration
├── utils/
│   ├── __init__.py
│   ├── validation.py                 # Input validation
│   ├── clean_running_submissions.py  # Fix stuck 'running' submissions
│   ├── remove_submission.py          # CLI tool to remove a submission by ID
│   └── reprocess_submissions.py      # Re-execute and re-score all submissions
├── tests/
│   └── ...                     # Unit tests
└── data/
    ├── california_housing.csv  # Ground truth data
    ├── submissions/            # Uploaded notebooks
    └── outputs/                # Executed notebooks
```


## 6. Contributing

Contributions are welcome. Please follow these guidelines:

- **Bug reports and feature requests**: Open a [GitHub Issue](https://github.com/gperdrizet/leaderboard/issues) describing the problem or proposal before starting work.
- **Pull requests**: Branch from `main`, make your changes, and ensure all tests pass locally before opening a PR:
  ```bash
  python3 -m unittest discover tests -v
  ```
  PRs are automatically tested on submission; they cannot be merged until the test suite passes.

Some areas for enhancement:

- More sophisticated scoring algorithms
- Better error handling and user feedback
- Additional security measures
- Performance optimizations
- UI/UX improvements


## 7. License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](https://github.com/gperdrizet/leaderboard/blob/main/LICENSE) file for full details.

In summary, you are free to use, modify, and distribute this software, but any derivative works must also be released under the GPL-3.0 license.
