# Super Simple Frontend Testing

## ONE Command to Test Everything:

```cmd
run_frontend.bat
```

That's it! This will:
- Start the mock API server
- Start the React app
- Open your browser automatically

## What to Test:

1. **Upload Files**: Use the files from `C:\dev\OptimoV2\data\base\`
2. **Submit Job**: Click submit after uploading
3. **Watch Progress**: See the job status update
4. **Download Results**: When job completes

## To Stop:
Press `Ctrl+C` twice in the terminal

## Troubleshooting:

If the browser doesn't open, manually go to: http://localhost:3000

If you see port errors, make sure no other apps are using ports 3000 or 5000.

---

**Note**: For production deployment, run `npm run build` in the optimo-frontend folder to create optimized files.