# Deployment Guide

## Deploy to Streamlit Cloud

### Prerequisites
- GitHub account
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))

### Steps

1. **Prepare your repository**
   ```bash
   # Initialize git (if not already done)
   git init
   
   # Add all files
   git add .
   
   # Create initial commit
   git commit -m "Initial commit: CFA Mistake Logger app"
   
   # Add GitHub remote (replace with your repo URL)
   git remote add origin https://github.com/yourusername/cfa-mistake-logger.git
   
   # Push to GitHub
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub account
   - Select your repository: `your-username/cfa-mistake-logger`
   - Set main file path: `app.py`
   - Click "Deploy!"

3. **App Configuration**
   - The app uses `.streamlit/config.toml` for configuration
   - No secrets required for basic functionality
   - CSV files are created automatically when users start logging mistakes

### File Structure for Deployment

```
cfa_logerror/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── .gitignore             # Git ignore rules
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── sample_data.csv        # Example data format
└── DEPLOYMENT.md          # This guide
```

### Environment Variables

No environment variables are required for basic deployment.

### Troubleshooting

1. **Build fails**: Check `requirements.txt` has correct versions
2. **App crashes on startup**: Verify `app.py` runs locally first
3. **Missing dependencies**: Add any missing packages to `requirements.txt`
4. **CSV write errors**: App handles file creation automatically

### Updates

To update your deployed app:
```bash
# Make changes locally
# Test locally: streamlit run app.py

# Commit and push changes
git add .
git commit -m "Description of changes"
git push

# Streamlit Cloud will auto-deploy the changes
```

### Performance Notes

- CSV files are stored in the app's temporary filesystem
- For persistent storage across deployments, consider using Streamlit's file system or external storage
- The app is optimized for personal use (single user sessions)

### Support

- Streamlit Cloud docs: [docs.streamlit.io](https://docs.streamlit.io)
- GitHub issues: Use the Issues tab in your repository
- Streamlit community: [discuss.streamlit.io](https://discuss.streamlit.io)