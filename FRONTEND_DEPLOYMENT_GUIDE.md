# Frontend Deployment to GitHub Pages

This guide walks you through deploying the OptimoV2 frontend to GitHub Pages.

## Prerequisites

1. A GitHub account
2. A GitHub repository for OptimoV2
3. Git installed and configured

## Step 1: Update package.json with your GitHub username

Edit `optimo-frontend/package.json` and update the homepage URL:

```json
"homepage": "https://YOUR_GITHUB_USERNAME.github.io/OptimoV2",
```

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

## Step 2: Build the production version

```bash
cd optimo-frontend
npm run build
```

This creates an optimized production build in the `build/` directory.

## Step 3: Deploy to GitHub Pages

### Option A: If your repository is already on GitHub

```bash
# Make sure you're in the optimo-frontend directory
cd optimo-frontend

# Deploy to GitHub Pages
npm run deploy
```

This command will:
- Build the project (if not already built)
- Create a `gh-pages` branch
- Push the build files to that branch
- Configure GitHub Pages to serve from that branch

### Option B: If you haven't pushed to GitHub yet

1. First, create a new repository on GitHub named `OptimoV2`

2. Initialize git and push your code:
```bash
# Go to the project root
cd C:\dev\OptimoV2

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit"

# Add your GitHub repository as origin
git remote add origin https://github.com/YOUR_USERNAME/OptimoV2.git

# Push to main branch
git push -u origin main
```

3. Now deploy the frontend:
```bash
cd optimo-frontend
npm run deploy
```

## Step 4: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click on "Settings" tab
3. Scroll down to "Pages" section in the left sidebar
4. Under "Source", select:
   - Source: Deploy from a branch
   - Branch: gh-pages
   - Folder: / (root)
5. Click "Save"

## Step 5: Access your deployed site

Your site will be available at:
```
https://YOUR_GITHUB_USERNAME.github.io/OptimoV2
```

It may take a few minutes for the site to become available.

## Important Notes

### About the Mock Data
- The deployed frontend will still use mock data (2 students)
- This is expected since there's no backend API yet
- The frontend serves as a demonstration of the UI/UX

### API Configuration
The frontend is configured to look for an API at the URL specified in the `REACT_APP_API_URL` environment variable. If not set, it defaults to `http://localhost:5000/api` (the mock server).

For production deployment with a real backend, you would:
1. Deploy your backend API (AWS or other cloud provider)
2. Update the build command to include the API URL:
   ```bash
   REACT_APP_API_URL=https://your-api-url.com/api npm run build
   npm run deploy
   ```

### Updating the Deployment

To update your deployed site after making changes:
```bash
cd optimo-frontend
npm run deploy
```

This will automatically update the gh-pages branch with your latest changes.

## Troubleshooting

### Error: "Failed to get remote.origin.url"
Make sure your git repository has a remote origin set:
```bash
git remote add origin https://github.com/YOUR_USERNAME/OptimoV2.git
```

### Error: "gh-pages branch already exists"
This is usually fine. The deployment will update the existing branch.

### Site not showing up
1. Check GitHub Pages settings are enabled
2. Wait 5-10 minutes for GitHub to build and deploy
3. Try clearing your browser cache
4. Check the Actions tab in your GitHub repository for any build errors

## Next Steps

Once deployed, you can:
1. Share the link for UI/UX feedback
2. Use it as a demonstration of the system's capabilities
3. Plan for backend API deployment to connect real data

Remember: This deployment shows the frontend interface only. To process real optimization data, you'll need to implement and deploy the backend API as described in `OPTIMOV2_DEPLOYMENT_PLAN.md`.