"""Streamlit application for Kaggle-style leaderboard.

This application allows students to upload Jupyter notebooks,
executes them automatically, scores the outputs, and displays
results on a public leaderboard.
"""

import streamlit as st
import os
from datetime import datetime
import tempfile
import shutil

from src.database import Database
from src.notebook_runner import NotebookRunner
from src.scorer import Scorer
from src.leaderboard import LeaderboardManager
from utils.validation import validate_submission


# Page configuration
st.set_page_config(
    page_title="Notebook Leaderboard",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = Database("data/leaderboard.db")
    st.session_state.notebook_runner = NotebookRunner("data/outputs", timeout_seconds=300)
    st.session_state.scorer = Scorer()
    st.session_state.leaderboard_manager = LeaderboardManager(st.session_state.db)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    """Main application function."""
    
    # Header
    st.markdown('<div class="main-header">🏆 Notebook Leaderboard 🏆</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Leaderboard", use_container_width=True)
        st.markdown("### Navigation")
        page = st.radio(
            "Select Page",
            ["🏠 Home & Submit", "📊 Leaderboard", "📈 My Stats", "ℹ️ About"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### Quick Stats")
        stats = st.session_state.leaderboard_manager.get_statistics()
        st.metric("Total Submissions", stats['total_submissions'])
        st.metric("Active Users", stats['total_users'])
        if stats['highest_score'] > 0:
            st.metric("Highest Score", f"{stats['highest_score']:.2f}")
    
    # Main content based on selected page
    if page == "🏠 Home & Submit":
        show_submission_page()
    elif page == "📊 Leaderboard":
        show_leaderboard_page()
    elif page == "📈 My Stats":
        show_stats_page()
    else:
        show_about_page()


def show_submission_page():
    """Display submission page."""
    st.markdown('<div class="sub-header">Submit Your Notebook</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Upload Instructions")
        st.write("""
        1. Enter your username
        2. Upload your Jupyter notebook (.ipynb file)
        3. Click 'Submit' to run and score your notebook
        4. Check the leaderboard to see your ranking!
        """)
        
        # Username input
        username = st.text_input(
            "Username",
            placeholder="Enter your username (3-50 characters)",
            help="Your username will appear on the leaderboard"
        )
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Notebook",
            type=['ipynb'],
            help="Upload your Jupyter notebook file (max 10MB)"
        )
        
        # Submit button
        if st.button("🚀 Submit", type="primary", use_container_width=True):
            if not username:
                st.error("⚠️ Please enter a username")
            elif not uploaded_file:
                st.error("⚠️ Please upload a notebook file")
            else:
                process_submission(username, uploaded_file)
    
    with col2:
        st.markdown("### Requirements")
        st.info("""
        **File Requirements:**
        - Must be a .ipynb file
        - Max size: 10MB
        - Must contain at least one code cell
        
        **Username Requirements:**
        - 3-50 characters
        - Letters, numbers, _, -, . only
        """)


def process_submission(username: str, uploaded_file):
    """Process a notebook submission.
    
    Args:
        username: Username of submitter
        uploaded_file: Uploaded file object
    """
    # Create temporary file for uploaded notebook
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ipynb') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        # Validate submission
        with st.spinner("Validating submission..."):
            is_valid, error_msg = validate_submission(tmp_path, username)
            
            if not is_valid:
                st.error(f"❌ Validation Error: {error_msg}")
                return
        
        st.success("✅ Validation passed!")
        
        # Save to submissions directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        submission_filename = f"{username}_{timestamp}.ipynb"
        submission_path = os.path.join("data/submissions", submission_filename)
        shutil.copy(tmp_path, submission_path)
        
        # Add to database
        submission_id = st.session_state.db.add_submission(
            username=username,
            notebook_path=submission_path,
            status="pending"
        )
        
        # Execute notebook
        with st.spinner("Executing notebook... This may take a few minutes."):
            st.session_state.db.update_submission(submission_id, "running")
            
            result = st.session_state.notebook_runner.execute_notebook_safe(submission_path)
            
            if result['success']:
                st.success(f"✅ Execution completed in {result['execution_time']:.2f} seconds")
                
                # Score the notebook
                with st.spinner("Scoring your submission..."):
                    score, feedback = st.session_state.scorer.score_notebook(
                        result['output_path']
                    )
                    
                    # Update database
                    st.session_state.db.update_submission(
                        submission_id,
                        status="completed",
                        score=score
                    )
                    
                    st.session_state.db.update_leaderboard(username, submission_id, score)
                    
                    # Display results
                    st.balloons()
                    st.success(f"🎉 Submission successful!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Your Score", f"{score:.2f}")
                    with col2:
                        rank_info = st.session_state.db.get_user_rank(username)
                        if rank_info:
                            rank, _ = rank_info
                            st.metric("Your Rank", f"#{rank}")
                    
                    if feedback:
                        st.info(f"**Feedback:** {feedback}")
            else:
                st.error(f"❌ Execution failed: {result['error_message']}")
                st.session_state.db.update_submission(
                    submission_id,
                    status="failed",
                    error_message=result['error_message']
                )
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def show_leaderboard_page():
    """Display leaderboard page."""
    st.markdown('<div class="sub-header">🏆 Leaderboard</div>', unsafe_allow_html=True)
    
    # Get leaderboard data
    df = st.session_state.leaderboard_manager.get_leaderboard_df()
    
    if df.empty:
        st.info("📊 No submissions yet. Be the first to submit!")
    else:
        # Add medals to top 3
        df_display = st.session_state.leaderboard_manager.format_leaderboard_for_display(df)
        
        # Display leaderboard
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", width="small"),
                "Username": st.column_config.TextColumn("Username", width="medium"),
                "Best Score": st.column_config.NumberColumn("Best Score", format="%.2f", width="small"),
                "Submissions": st.column_config.NumberColumn("Submissions", width="small"),
                "Last Updated": st.column_config.TextColumn("Last Updated", width="medium")
            }
        )
        
        # Recent activity
        st.markdown("### 📝 Recent Submissions")
        recent_df = st.session_state.leaderboard_manager.get_recent_submissions_df(limit=10)
        st.dataframe(recent_df, use_container_width=True, hide_index=True)


def show_stats_page():
    """Display user statistics page."""
    st.markdown('<div class="sub-header">📈 My Statistics</div>', unsafe_allow_html=True)
    
    username = st.text_input("Enter your username to view stats", placeholder="Username")
    
    if username:
        if st.button("View Stats"):
            stats = st.session_state.leaderboard_manager.get_user_stats(username)
            
            if not stats:
                st.warning(f"No submissions found for user '{username}'")
            else:
                # Display stats in columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown('<div class="stat-box">', unsafe_allow_html=True)
                    st.markdown(f'<div class="stat-value">#{stats["rank"]}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="stat-label">Current Rank</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="stat-box">', unsafe_allow_html=True)
                    st.markdown(f'<div class="stat-value">{stats["best_score"]:.2f}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="stat-label">Best Score</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="stat-box">', unsafe_allow_html=True)
                    st.markdown(f'<div class="stat-value">{stats["total_submissions"]}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="stat-label">Total Submissions</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    st.markdown('<div class="stat-box">', unsafe_allow_html=True)
                    st.markdown(f'<div class="stat-value">{stats["average_score"]:.2f}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="stat-label">Average Score</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Submission history
                st.markdown("### 📋 Submission History")
                history_df = st.session_state.leaderboard_manager.get_submission_history_df(username)
                st.dataframe(history_df, use_container_width=True, hide_index=True)


def show_about_page():
    """Display about page."""
    st.markdown('<div class="sub-header">ℹ️ About This Leaderboard</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to the Notebook Leaderboard!
    
    This is a Kaggle-style leaderboard system for Jupyter notebook submissions.
    
    #### How It Works
    
    1. **Submit**: Upload your Jupyter notebook with your solution
    2. **Execute**: The system automatically runs your notebook
    3. **Score**: Your output is evaluated and scored
    4. **Rank**: See where you stand on the leaderboard!
    
    #### Scoring
    
    Your notebook is scored based on:
    - Successful execution (all cells run without errors)
    - Output accuracy (compared against expected results)
    - Code quality and completeness
    
    #### Tips for Success
    
    - Test your notebook locally before submitting
    - Ensure all cells execute without errors
    - Follow the assignment requirements carefully
    - Check your score and improve your solution
    - You can submit multiple times - only your best score counts!
    
    #### Technical Details
    
    - **Execution Timeout**: 5 minutes
    - **Max File Size**: 10MB
    - **Supported Format**: Jupyter Notebook (.ipynb)
    - **Kernel**: Python 3
    
    ---
    
    Built with ❤️ using Streamlit
    """)


if __name__ == "__main__":
    main()
