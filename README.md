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


## Features

- **Upload Notebooks**: Students can upload Jupyter notebooks through a web interface
- **Automatic Execution**: Notebooks are executed automatically in a sandboxed environment
- **Scoring System**: Outputs are evaluated and scored based on customizable criteria
- **Live Leaderboard**: Public leaderboard showing rankings in real-time
- **User Statistics**: Track individual submission history and performance
- **Validation**: Built-in validation for file format, size, and structure

## Using the leaderboard

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


## Running the leaderboard locally (development set-up)

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


## Customizing the Scoring Function

The scoring logic is in `src/scorer.py`. Customize the `score_notebook()` method to match your assignment requirements:

```python
def score_notebook(self, executed_notebook_path: str, output_data: Optional[Dict] = None) -> Tuple[float, str]:
    # Add your custom scoring logic here
    score = 0.0
    feedback = "Your feedback here"
    return score, feedback
```


## Admin Panel

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


## Execution Timeout

Default timeout is 5 minutes. Change it in `app.py`:

```python
st.session_state.notebook_runner = NotebookRunner("data/outputs", timeout_seconds=300)
```


## File Size Limit

Default max file size is 10MB. Change it in `utils/validation.py`:

```python
validator = NotebookValidator(max_file_size_mb=10.0)
```


## Streamlit Configuration

Modify `.streamlit/config.toml` to customize the app appearance and behavior.


## Maintenance Utilities

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


## Deployment to HuggingFace Spaces

### 1. Create a HuggingFace Space

Go to [huggingface.co/spaces](https://huggingface.co/spaces) → **New Space**.
- SDK: **Streamlit**
- Visibility: Public (or Private)


### 2. Create a database dataset repository

The submission database is persisted in a separate HuggingFace dataset repo so it survives redeployments.

Go to [huggingface.co/new-dataset](https://huggingface.co/new-dataset):
- Set visibility to **Private**
- Note the repo ID (e.g. `your-username/leaderboard-db`)


### 3. Create an access token

Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → **Create new token**:
- Type: **Fine-grained**
- Grant **Write** access to both the Space repo and the dataset repo


### 4. Add Space Secrets

In your Space → **Settings → Variables and secrets**, add:

| Secret | Value |
|---|---|
| `HF_TOKEN` | The token from step 3 |
| `HF_DB_REPO` | Dataset repo ID, e.g. `your-username/leaderboard-db` |
| `ADMIN_PIN` | A secure PIN for the admin panel (6+ characters) |


### 5. Configure GitHub Actions deployment (optional)

To enable automatic deployment on push to `main`, add the same token as a GitHub repository secret named `LEADERBOARD_GITHUB_DEPLOYMENT` (**Settings → Secrets and variables → Actions**).


### 6. Deploy

Push to `main` (triggers the GitHub Actions workflow) or upload files directly to the Space. On first startup the app creates a fresh database and pushes it to the dataset repo. All subsequent restarts pull the latest database from the dataset repo automatically.


## Project Structure

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
│   ├── validation.py         # Input validation
│   ├── clean_running_submissions.py  # Fix stuck 'running' submissions
│   ├── remove_submission.py          # CLI tool to remove a submission by ID
│   └── reprocess_submissions.py     # Re-execute and re-score all submissions
├── tests/
│   └── ...                   # Unit tests
└── data/
    ├── california_housing.csv  # Ground truth data
    ├── submissions/            # Uploaded notebooks
    └── outputs/                # Executed notebooks
```


## Technical Details

### Database Schema

**submissions table:**
- `id`: Primary key
- `username`: Username of submitter
- `timestamp`: Submission time
- `notebook_path`: Path to uploaded notebook
- `score`: Score (if completed)
- `status`: 'pending', 'running', 'completed', or 'failed'
- `error_message`: Error details (if failed)

**leaderboard table:**
- `username`: Primary key
- `best_score`: Highest score achieved
- `best_submission_id`: ID of best submission
- `last_updated`: Last submission time
- `submission_count`: Total number of submissions


### Security Considerations

**Important**: This application executes user-submitted code. For production use:

1. **Run in a sandboxed environment** (e.g., Docker container)
2. **Set resource limits** (CPU, memory, disk)
3. **Use network isolation** to prevent external access
4. **Enable execution timeout** (already implemented)
5. **Sanitize all inputs** (already implemented for basic cases)


### HuggingFace Spaces Limitations

- **Database persistence**: Handled via a HuggingFace Hub dataset repo — the database is pulled on startup and pushed after every write. See deployment steps above.
- **Execution time**: May have timeout limits for long-running notebooks. Adjust `timeout_seconds` in `app.py` accordingly.
- **Resources**: Limited CPU/RAM on free-tier Spaces. Complex notebooks may hit memory limits.


## Troubleshooting

### Notebooks fail to execute

- Check that the notebook runs locally with Python 3
- Ensure all required packages are in `requirements.txt`
- Check execution logs in the database or console


### Scoring returns 0

- Verify your scoring function in `src/scorer.py`
- Check that the notebook produces expected outputs
- Add debug logging to the scoring function


### Database errors

- Ensure `data/` directory exists and is writable
- Check SQLite permissions
- For HuggingFace Spaces, verify the `HF_TOKEN` and `HF_DB_REPO` Space Secrets are set correctly


## Dependencies

- **Streamlit**: Web interface framework
- **Pandas**: Data manipulation
- **Papermill**: Notebook execution
- **nbformat/nbconvert**: Notebook parsing
- **SQLite3**: Database (built-in with Python)
- **huggingface_hub**: Database persistence across HuggingFace Space restarts


## Contributing

Feel free to customize this application for your specific needs. Some areas for enhancement:

- More sophisticated scoring algorithms
- Better error handling and user feedback
- Additional security measures
- Performance optimizations
- UI/UX improvements


## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](https://github.com/gperdrizet/leaderboard/blob/main/LICENSE) file for full details.

In summary, you are free to use, modify, and distribute this software, but any derivative works must also be released under the GPL-3.0 license.
