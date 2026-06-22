# Admin Panel Guide

## Overview

The admin panel allows instructors to manage submissions in the leaderboard application. Access is protected by a PIN that must be configured as an environment variable.

## Setup

### 1. Configure Persistent Database (HuggingFace Spaces)

By default, the SQLite database is stored on the Space's ephemeral filesystem and is lost on each redeployment. To persist the database across deployments, configure a HuggingFace Hub dataset repository as the backing store.

**Step 1 — Create a dataset repository** on [HuggingFace Hub](https://huggingface.co/new-dataset). It can be private. Note the repo ID (e.g. `your-username/leaderboard-db`).

**Step 2 — Create a fine-grained access token** at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) with **write** access to that dataset repo.

**Step 3 — Add two Space Secrets** in your Space settings (`Settings → Variables and secrets`):

| Secret name | Value |
|---|---|
| `HF_TOKEN` | The token from step 2 |
| `HF_DB_REPO` | The dataset repo ID, e.g. `your-username/leaderboard-db` |

Once both secrets are set the app will:
- Download `leaderboard.db` from the dataset repo on every startup
- Upload the updated `leaderboard.db` back after every write operation (new submission, score update, leaderboard change)

If either secret is missing the app runs in **local-only mode** — suitable for local development.

### 2. Set the Admin PIN

Choose one of these methods:

**Option A: Environment Variable (Recommended for production)**
```bash
export ADMIN_PIN=your_secure_pin
```

**Option B: .env File (Recommended for development)**
```bash
echo "ADMIN_PIN=your_secure_pin" > .env
```

**Option C: Streamlit Secrets (For HuggingFace Spaces)**

Create `.streamlit/secrets.toml`:
```toml
ADMIN_PIN = "your_secure_pin"
```

Then access it in the app:
```python
admin_pin = st.secrets.get("ADMIN_PIN", os.environ.get('ADMIN_PIN', ''))
```

### 3. Choose a Secure PIN

- Use at least 6 characters
- Mix letters and numbers for better security
- Avoid common patterns (e.g., "123456", "admin")
- Keep the PIN confidential

## Usage

### Accessing the Admin Panel

1. Start the application
2. Click on "Admin" in the sidebar navigation
3. Enter the admin PIN when prompted
4. Click "Login"

### Managing Submissions

Once authenticated, you can:

1. **View All Submissions**
   - See a table with all submissions
   - Columns: ID, Username, Score, Status, Timestamp
   - Sorted by submission ID

2. **Remove a Submission**
   - Enter the submission ID you want to remove
   - Click "Remove Submission"
   - Review the confirmation details
   - Click "Yes, Remove" to confirm

### What Happens When You Remove a Submission

- The submission is permanently deleted from the database
- The leaderboard is automatically recalculated for that user
- If the user has other completed submissions, their best score is updated
- If the user has no remaining completed submissions, they are removed from the leaderboard
- All actions are logged for audit purposes

### Logging Out

Click the "Logout" button in the top-right corner to end your admin session.

## Security Notes

- Admin authentication is session-based (stored in Streamlit's session state)
- Sessions expire when you close the browser or reload the page
- Failed login attempts are logged
- The PIN is never stored in the database or displayed in the UI
- All admin actions are logged with timestamps

## Troubleshooting

### "Admin access is not configured"

- Make sure the `ADMIN_PIN` environment variable is set
- Restart the application after setting the environment variable
- Check that your `.env` file is in the correct location

### Cannot Access After Setting PIN

- Verify the environment variable is set: `echo $ADMIN_PIN`
- Make sure there are no extra spaces in the PIN
- Try restarting the Streamlit application

### Incorrect PIN Error

- Double-check your PIN (case-sensitive)
- Verify you're using the correct PIN that was set
- Check the logs for failed login attempts

## Example Workflow

```bash
# 1. Set admin PIN
export ADMIN_PIN=MySecurePin123

# 2. Start the application
streamlit run app.py

# 3. In browser:
#    - Navigate to "Admin" page
#    - Enter: MySecurePin123
#    - Click "Login"

# 4. View submissions and remove as needed
```

## Best Practices

1. **Change the default PIN** - Never use example PINs from documentation
2. **Use strong PINs** - Combine letters, numbers, and symbols
3. **Don't share the PIN** - Keep it confidential among administrators
4. **Rotate regularly** - Change the PIN periodically
5. **Monitor logs** - Check for unauthorized access attempts
6. **Backup before bulk operations** - Consider backing up the database before removing many submissions
