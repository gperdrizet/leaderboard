"""Streamlit application for Kaggle-style leaderboard.

This application allows students to upload Jupyter notebooks,
executes them automatically, scores the outputs, and displays
results on a public leaderboard.
"""

import os
import shutil
import tempfile
from datetime import datetime

import streamlit as st

from src.database import Database
from src.notebook_runner import NotebookRunner
from src.scorer import Scorer
from src.leaderboard import LeaderboardManager
from src.logger import get_logger, configure_warnings_logging
from utils.validation import validate_submission

# Configure warnings to be captured in logs
configure_warnings_logging()

logger = get_logger(__name__)


# Page configuration
st.set_page_config(
    page_title="Notebook Leaderboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db' not in st.session_state:
    logger.info("Initializing application session state")
    st.session_state.db = Database("data/leaderboard.db")
    st.session_state.notebook_runner = NotebookRunner("data/outputs", timeout_seconds=300)
    st.session_state.scorer = Scorer(ground_truth_path="data/california_housing.csv")
    st.session_state.leaderboard_manager = LeaderboardManager(st.session_state.db)
    logger.info("Application initialized successfully")

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
    st.markdown('<div class="main-header">Notebook Leaderboard</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:

        # st.image(
        #     "https://via.placeholder.com/300x100/1f77b4/ffffff?text=Leaderboard"
        # )

        st.markdown("### Navigation")

        page = st.radio(
            "Select Page",
            ["Home & Submit", "Leaderboard", "User Stats", "About", "Admin"],
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
    if page == "Home & Submit":
        show_submission_page()

    elif page == "Leaderboard":
        show_leaderboard_page()

    elif page == "User Stats":
        show_stats_page()

    elif page == "Admin":
        show_admin_page()

    else:
        show_about_page()


def show_submission_page():
    """Display submission page."""

    st.markdown(
        '<div class="sub-header">Submit Your Notebook</div>',
        unsafe_allow_html=True
    )

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
        if st.button("Submit", type="primary"):

            if not username:
                st.error("Please enter a username")

            elif not uploaded_file:
                st.error("Please upload a notebook file")

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
    logger.info(f"Processing submission from user '{username}', file: {uploaded_file.name}")

    # Create temporary file for uploaded notebook
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ipynb') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:

        # Validate submission
        with st.spinner("Validating submission..."):
            is_valid, error_msg = validate_submission(tmp_path, username)

            if not is_valid:
                logger.warning(f"Validation failed for '{username}': {error_msg}")
                st.error(f"Validation Error: {error_msg}")
                return

        logger.info(f"Validation passed for '{username}'")
        st.success("Validation passed!")

        # Save to submissions directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        submission_filename = f"{username}_{timestamp}.ipynb"
        submission_path = os.path.join("data/submissions", submission_filename)
        shutil.copy(tmp_path, submission_path)
        logger.info(f"Saved submission to: {submission_path}")

        # Add to database
        submission_id = st.session_state.db.add_submission(
            username=username,
            notebook_path=submission_path,
            status="pending"
        )

        # Execute notebook
        with st.spinner("Executing notebook... This may take a few minutes."):

            st.session_state.db.update_submission(submission_id, "running")
            logger.info(f"Starting execution for submission ID {submission_id}")
            result = st.session_state.notebook_runner.execute_notebook_safe(submission_path)

            if result['success']:
                logger.info(f"Execution successful for submission ID {submission_id} in {result['execution_time']:.2f}s")
                st.success(f"Execution completed in {result['execution_time']:.2f} seconds")

                # Score the notebook
                with st.spinner("Scoring your submission..."):
                    score, scoring_error = st.session_state.scorer.score_notebook(
                        result['output_path']
                    )

                    # Check if scoring failed (0.0 with error message)
                    if scoring_error:
                        logger.error(f"Scoring failed for submission ID {submission_id}: {scoring_error}")
                        st.error(f"Submission failed: {scoring_error}")
                        
                        st.session_state.db.update_submission(
                            submission_id,
                            status="failed",
                            error_message=scoring_error
                        )
                    else:
                        # Update database with successful score
                        st.session_state.db.update_submission(
                            submission_id,
                            status="completed",
                            score=score
                        )

                        st.session_state.db.update_leaderboard(username, submission_id, score)
                        
                        logger.info(f"Submission ID {submission_id} completed with score {score}")
                        
                        # Display results
                        st.balloons()
                        st.success("Submission successful!")

                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric("Your Score", f"{score:.2f}")

                        with col2:
                            rank_info = st.session_state.db.get_user_rank(username)

                            if rank_info:
                                rank, _ = rank_info
                                st.metric("Your Rank", f"#{rank}")
                                logger.info(f"User '{username}' ranked #{rank} with score {score}")
            else:

                logger.error(f"Execution failed for submission ID {submission_id}: {result['error_message']}")
                st.error(f"Execution failed: {result['error_message']}")

                st.session_state.db.update_submission(
                    submission_id,
                    status="failed",
                    error_message=result['error_message']
                )

    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            logger.debug(f"Cleaned up temporary file: {tmp_path}")


def show_leaderboard_page():
    """Display leaderboard page."""

    st.markdown('<div class="sub-header">Leaderboard</div>', unsafe_allow_html=True)

    # Get leaderboard data
    df = st.session_state.leaderboard_manager.get_leaderboard_df()

    if df.empty:
        st.info("No submissions yet. Be the first to submit!")

    else:
        # Add medals to top 3
        df_display = st.session_state.leaderboard_manager.format_leaderboard_for_display(df)

        # Display leaderboard
        st.dataframe(
            df_display,
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
        st.markdown("### Recent Submissions")
        recent_df = st.session_state.leaderboard_manager.get_recent_submissions_df(limit=10)
        st.dataframe(recent_df, hide_index=True)


def show_stats_page():
    """Display user statistics page."""

    st.markdown('<div class="sub-header">User Statistics</div>', unsafe_allow_html=True)

    username = st.text_input("Enter a username to view their stats", placeholder="Username")

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
                st.markdown("### Submission History")
                history_df = st.session_state.leaderboard_manager.get_submission_history_df(username)
                st.dataframe(history_df, hide_index=True)


def show_about_page():
    """Display about page."""

    st.markdown('<div class="sub-header">About This Leaderboard</div>', unsafe_allow_html=True)

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
    """)


def show_admin_page():
    """Display admin page with PIN protection."""
    st.markdown('<div class="sub-header">Admin Panel</div>', unsafe_allow_html=True)
    
    # Get admin PIN from environment variable
    admin_pin = os.environ.get('ADMIN_PIN', '')
    
    # Also check Streamlit secrets (for HuggingFace Spaces)
    if not admin_pin and hasattr(st, 'secrets') and 'ADMIN_PIN' in st.secrets:
        admin_pin = st.secrets['ADMIN_PIN']
    
    if not admin_pin:
        st.error("Admin access is not configured. Please set the ADMIN_PIN environment variable.")
        logger.warning("Admin page accessed but ADMIN_PIN not configured")
        return
    
    # Check if user is authenticated
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        # Show PIN entry form
        st.markdown("### Admin Authentication")
        st.info("Enter the admin PIN to access administrative functions.")
        
        pin_input = st.text_input("Admin PIN", type="password", key="admin_pin_input")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Login", type="primary"):
                if pin_input == admin_pin:
                    st.session_state.admin_authenticated = True
                    logger.info("Admin authenticated successfully")
                    st.rerun()
                else:
                    st.error("Incorrect PIN")
                    logger.warning("Failed admin login attempt")
        
        return
    
    # User is authenticated, show admin panel
    st.success("✓ Authenticated as Administrator")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.admin_authenticated = False
            logger.info("Admin logged out")
            st.rerun()
    
    st.markdown("---")
    st.markdown("### Manage Submissions")
    
    # Get all submissions
    all_submissions = st.session_state.db.get_all_submissions()
    
    if not all_submissions:
        st.info("No submissions in the database.")
        return
    
    # Display submissions table
    st.markdown(f"**Total Submissions:** {len(all_submissions)}")
    
    # Convert to DataFrame for display
    import pandas as pd
    df = pd.DataFrame(all_submissions)
    
    # Format the display
    display_df = df[['id', 'username', 'score', 'status', 'timestamp']].copy()
    display_df['score'] = display_df['score'].apply(lambda x: f"{x:.2f}" if x is not None else "N/A")
    display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    st.dataframe(
        display_df,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "username": st.column_config.TextColumn("Username", width="medium"),
            "score": st.column_config.TextColumn("Score", width="small"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
        },
        width="stretch"
    )
    
    st.markdown("---")
    st.markdown("### Remove Submission")
    
    # Initialize session state for removal confirmation
    if 'confirm_removal_id' not in st.session_state:
        st.session_state.confirm_removal_id = None
    
    # Submission removal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        submission_id_input = st.number_input(
            "Submission ID to remove",
            min_value=1,
            step=1,
            help="Enter the ID of the submission you want to remove",
            key="removal_id_input"
        )
    
    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("Remove Submission", type="secondary", key="remove_btn"):
            # Store the ID to confirm
            st.session_state.confirm_removal_id = submission_id_input
            st.rerun()
    
    # Show confirmation dialog if a removal is pending
    if st.session_state.confirm_removal_id is not None:
        submission_id = st.session_state.confirm_removal_id
        
        # Get submission details
        submission = st.session_state.db.get_submission(submission_id)
        
        if not submission:
            st.error(f"Submission ID {submission_id} not found.")
            logger.warning(f"Attempt to remove non-existent submission ID {submission_id}")
            st.session_state.confirm_removal_id = None
        else:
            username = submission['username']
            score = submission['score']
            status = submission['status']
            
            # Show confirmation
            st.warning(f"""⚠️ Confirm Removal
            
**Submission ID:** {submission_id}  
**Username:** {username}  
**Score:** {score if score is not None else 'N/A'}  
**Status:** {status}

This action cannot be undone.
            """)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("✓ Yes, Remove", type="primary", key=f"confirm_remove_{submission_id}"):
                    logger.info(f"Admin confirmed removal of submission ID {submission_id}")
                    try:
                        # Delete from submissions table
                        with st.session_state.db._get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
                            
                            # Update leaderboard - recalculate best score for this user
                            cursor.execute('''
                                SELECT MAX(score) as best_score, COUNT(*) as count
                                FROM submissions 
                                WHERE username = ? AND status = 'completed'
                            ''', (username,))
                            
                            leaderboard_data = cursor.fetchone()
                            
                            if leaderboard_data['best_score'] is not None:
                                # User still has completed submissions
                                cursor.execute('''
                                    SELECT id FROM submissions 
                                    WHERE username = ? AND score = ? AND status = 'completed'
                                    LIMIT 1
                                ''', (username, leaderboard_data['best_score']))
                                
                                best_submission_id = cursor.fetchone()['id']
                                
                                cursor.execute('''
                                    UPDATE leaderboard 
                                    SET best_score = ?, submission_count = ?, best_submission_id = ?, last_updated = ?
                                    WHERE username = ?
                                ''', (leaderboard_data['best_score'], leaderboard_data['count'], best_submission_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), username))
                                
                                logger.info(f"Removed submission ID {submission_id}, updated leaderboard for {username}")
                            else:
                                # User has no more completed submissions
                                cursor.execute('DELETE FROM leaderboard WHERE username = ?', (username,))
                                logger.info(f"Removed submission ID {submission_id}, removed {username} from leaderboard")
                        
                        # Clear confirmation state and show success
                        st.session_state.confirm_removal_id = None
                        st.success(f"✓ Successfully removed submission ID {submission_id}")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error removing submission: {e}")
                        logger.error(f"Error removing submission ID {submission_id}: {e}", exc_info=True)
                        st.session_state.confirm_removal_id = None
            
            with col2:
                if st.button("✗ Cancel", key=f"cancel_remove_{submission_id}"):
                    st.session_state.confirm_removal_id = None
                    st.info("Removal cancelled.")
                    st.rerun()


if __name__ == "__main__":
    main()
