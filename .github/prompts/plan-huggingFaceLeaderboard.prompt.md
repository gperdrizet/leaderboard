# HuggingFace Space Kaggle-Style Leaderboard Plan

## Project Overview
Build a Kaggle-style leaderboard application hosted on HuggingFace Spaces where students can upload Jupyter notebooks, which are then executed and scored automatically. Results are displayed on a public leaderboard.

## Architecture Components

### 1. Frontend (Streamlit Interface)
- **Upload Interface**: Allow students to upload `.ipynb` files using `st.file_uploader()`
- **Leaderboard Display**: Show ranked scores with student names/IDs using `st.dataframe()` or `st.table()`
- **Submission History**: Display past submissions for each user
- **Status Indicators**: Show processing status (pending, running, completed, failed) using `st.status()` or `st.spinner()`

### 2. Backend Components

#### Notebook Runner (`src/notebook_runner.py`)
- Execute uploaded Jupyter notebooks in isolated environment
- Handle notebook execution with timeout limits
- Capture outputs and results
- Error handling for failed executions
- Security: sandboxed execution to prevent malicious code

#### Scorer (`src/scorer.py`)
- Define scoring function/metrics
- Evaluate notebook outputs against ground truth
- Return numerical score and optional feedback
- Support multiple evaluation metrics if needed

#### Leaderboard Manager (`src/leaderboard.py`)
- Maintain leaderboard state
- Sort and rank submissions
- Handle ties and duplicate submissions
- Update leaderboard after each successful submission

#### Database Handler (`src/database.py`)
- Store submission metadata (timestamp, user, score, status)
- Persist leaderboard data using SQLite
- Database schema with tables for submissions and leaderboard
- Track submission history per user
- Handle database connections and transactions

#### Validation (`utils/validation.py`)
- Validate notebook format and structure
- Check for required cells/outputs
- File size limits

### 3. Data Storage Structure
```
data/
├── submissions/          # Uploaded notebooks
│   ├── user1_timestamp1.ipynb
│   └── user2_timestamp1.ipynb
├── outputs/             # Execution outputs
│   ├── user1_timestamp1_output.pkl
│   └── user2_timestamp1_output.pkl
└── leaderboard.db       # SQLite database
```

#### Database Schema
**submissions table:**
- id (PRIMARY KEY, AUTOINCREMENT)
- username (TEXT)
- timestamp (DATETIME)
- notebook_path (TEXT)
- score (REAL)
- status (TEXT: 'pending', 'running', 'completed', 'failed')
- error_message (TEXT, nullable)

**leaderboard table:**
- username (PRIMARY KEY)
- best_score (REAL)
- best_submission_id (INTEGER, FOREIGN KEY)
- last_updated (DATETIME)
- submission_count (INTEGER)

### 4. Main Application (`app.py`)
- Streamlit app setup and configuration
- Integrate all components
- Define UI layout with Streamlit components (columns, tabs, expanders)
- Handle file uploads and processing workflow
- Implement session state for user interactions

## Key Features to Implement

### Core Features
1. **Notebook Upload**: Drag-and-drop or file browser
2. **Automated Execution**: Run notebook in isolated environment
3. **Scoring**: Apply scoring function to outputs
4. **Leaderboard Display**: Real-time ranked list
5. **User Identification**: Username/student ID input

### Additional Features (Optional)
1. **Best Score Tracking**: Keep only best score per user
2. **Execution Logs**: Show errors if notebook fails
3. **Download Results**: Allow users to download execution logs
4. **Admin Panel**: Ability to reset leaderboard or remove entries
5. **Timestamps**: Show submission date/time

## Technical Stack

### Core Dependencies
- **Streamlit**: Web interface framework
- **nbconvert/nbformat**: Parse and execute Jupyter notebooks
- **papermill**: Execute notebooks programmatically
- **pandas**: Data manipulation for leaderboard
- **sqlite3**: Database (built-in with Python)

### Security Considerations
- **Execution Timeout**: Prevent infinite loops (e.g., 5-minute max)
- **Resource Limits**: Limit memory and CPU usage
- **Code Sandboxing**: Use containers or restricted environments
- **Input Validation**: Sanitize all user inputs
- **Rate Limiting**: Prevent abuse

## Implementation Steps

### Phase 1: Basic Setup
1. Initialize HuggingFace Space with Streamlit
2. Create basic file upload interface with `st.file_uploader()`
3. Implement simple notebook execution
4. Create basic scoring function
5. Display results in table using `st.dataframe()`

### Phase 2: Leaderboard & Database
1. Create SQLite database schema
2. Implement database handler with CRUD operations
3. Add ranking and sorting logic
4. Persist submissions and leaderboard to SQLite
5. Display formatted leaderboard in UI

### Phase 3: Enhancements
1. Add user identification
2. Implement submission validation
3. Add error handling and user feedback
4. Add execution logs display

### Phase 4: Polish
1. Improve UI/UX design
2. Add timestamps and metadata
3. Implement admin features
4. Add documentation and help text
5. Testing and deployment

## File Structure
```
.
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # Documentation
├── .streamlit/
│   └── config.toml           # Streamlit configuration
├── src/
│   ├── __init__.py
│   ├── notebook_runner.py    # Notebook execution engine
│   ├── scorer.py             # Scoring logic
│   ├── leaderboard.py        # Leaderboard management
│   └── database.py           # Data persistence
├── utils/
│   ├── __init__.py
│   └── validation.py         # Input validation
└── data/
    ├── submissions/          # Uploaded notebooks
    ├── outputs/              # Execution results
    └── leaderboard.db        # SQLite database
```

## Configuration Considerations
- **Scoring Function**: Must be customizable for different assignments
- **Ground Truth Data**: Where to store expected outputs
- **Execution Environment**: Ensure consistent package versions
- **Timeout Settings**: Balance between allowing complex code and preventing abuse
- **Storage Limits**: HuggingFace Spaces has storage constraints

## Example Workflow
1. Student uploads notebook with username
2. System validates notebook format
3. System executes notebook with timeout
4. Scoring function evaluates outputs
5. Score is added to leaderboard
6. Leaderboard is updated and displayed
7. Student sees their rank and score
