# Notebook Leaderboard

A Kaggle-style leaderboard application for Jupyter notebook submissions, built with Streamlit and designed to run on HuggingFace Spaces.

## Features

- **Upload Notebooks**: Students can upload Jupyter notebooks through a web interface
- **Automatic Execution**: Notebooks are executed automatically in a sandboxed environment
- **Scoring System**: Outputs are evaluated and scored based on customizable criteria
- **Live Leaderboard**: Public leaderboard showing rankings in real-time
- **User Statistics**: Track individual submission history and performance
- **Validation**: Built-in validation for file format, size, and structure

## Quick Start

### Local Installation

1. **Clone or download this repository**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
streamlit run app.py
```

4. **Open your browser** to `http://localhost:8501`

### Deployment on HuggingFace Spaces

1. **Create a new Space** on [HuggingFace](https://huggingface.co/spaces)
   - Select "Streamlit" as the SDK
   
2. **Upload all files** from this repository to your Space

3. **The app will automatically deploy** and be accessible at your Space's URL

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
│   ├── database.py           # SQLite database operations
│   ├── notebook_runner.py    # Notebook execution engine
│   ├── scorer.py             # Scoring logic
│   └── leaderboard.py        # Leaderboard management
├── utils/
│   ├── __init__.py
│   └── validation.py         # Input validation
└── data/
    ├── submissions/          # Uploaded notebooks
    ├── outputs/              # Execution results
    └── leaderboard.db        # SQLite database
```

## Configuration

### Scoring Function

The scoring logic is in `src/scorer.py`. Customize the `score_notebook()` method to match your assignment requirements:

```python
def score_notebook(self, executed_notebook_path: str, output_data: Optional[Dict] = None) -> Tuple[float, str]:
    # Add your custom scoring logic here
    score = 0.0
    feedback = "Your feedback here"
    return score, feedback
```

### Execution Timeout

Default timeout is 5 minutes. Change it in `app.py`:

```python
st.session_state.notebook_runner = NotebookRunner("data/outputs", timeout_seconds=300)
```

### File Size Limit

Default max file size is 10MB. Change it in `utils/validation.py`:

```python
validator = NotebookValidator(max_file_size_mb=10.0)
```

### Streamlit Configuration

Modify `.streamlit/config.toml` to customize the app appearance and behavior.

## Usage

### For Students

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

### For Instructors

#### Customizing the Scoring Function

1. Open `src/scorer.py`
2. Modify the `score_notebook()` method
3. Add ground truth data if needed:
   ```python
   scorer = Scorer(ground_truth_path="path/to/ground_truth.json")
   ```

#### Using Scrapbook for Variable Extraction

For better variable extraction from notebooks, students can use [scrapbook](https://github.com/nteract/scrapbook):

In student notebooks:
```python
import scrapbook as sb

# Record outputs
sb.glue("accuracy", 0.95)
sb.glue("predictions", my_predictions)
```

In `src/scorer.py`:
```python
import scrapbook as sb

# Read notebook
notebook = sb.read_notebook(executed_notebook_path)
accuracy = notebook.scraps['accuracy'].data
predictions = notebook.scraps['predictions'].data
```

#### Admin Functions

Access admin functions programmatically:

```python
from src.database import Database
from src.leaderboard import LeaderboardManager

db = Database()
lm = LeaderboardManager(db)

# Clear all data (use with caution!)
lm.clear_all_data()

# Get all submissions
submissions = db.get_all_submissions()

# Export leaderboard
leaderboard_df = lm.get_leaderboard_df()
leaderboard_df.to_csv("leaderboard_export.csv")
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
6. **Consider using additional security tools** like:
   - RestrictedPython for code execution
   - Docker for containerization
   - Resource limiting with cgroups

### HuggingFace Spaces Limitations

- **Storage**: Limited persistent storage (use external storage if needed)
- **Execution Time**: May have timeout limits for long-running processes
- **Resources**: Limited CPU/RAM (adjust timeout accordingly)

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
- For HuggingFace Spaces, ensure persistent storage is configured

## Dependencies

- **Streamlit**: Web interface framework
- **Pandas**: Data manipulation
- **Papermill**: Notebook execution
- **nbformat/nbconvert**: Notebook parsing
- **SQLite3**: Database (built-in with Python)

## Contributing

Feel free to customize this application for your specific needs. Some areas for enhancement:

- More sophisticated scoring algorithms
- Better error handling and user feedback
- Additional security measures
- Performance optimizations
- UI/UX improvements

## License

This project is open source and available for educational use.
