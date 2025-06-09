# AWS Configuration Note

## Why is aws-config.ts in the src directory?

Create React App (CRA) doesn't allow importing files from outside the `src/` directory for security and build optimization reasons. 

## Current Setup

1. **Original config location**: `/config/aws_config.json` (for backend use)
2. **Frontend config location**: `/optimo-frontend/src/aws-config.ts` (for frontend use)

## Best Practices for Production

In a production environment, you should:

1. **Use environment variables** instead of hardcoded values:
   ```typescript
   const awsConfig = {
     region: process.env.REACT_APP_AWS_REGION || "us-west-2",
     buckets: {
       input: process.env.REACT_APP_INPUT_BUCKET || "optimo-input-files",
       output: process.env.REACT_APP_OUTPUT_BUCKET || "optimo-output-files"
     },
     api: {
       baseUrl: process.env.REACT_APP_API_BASE_URL || "https://ppwbzsy1bh.execute-api.us-west-2.amazonaws.com/prod"
     }
   };
   ```

2. **Set environment variables** during build:
   ```bash
   REACT_APP_API_BASE_URL=https://your-api.com npm run build
   ```

3. **Keep sensitive information** out of the repository

## Updating Configuration

If you need to update the AWS configuration:
1. Update `/config/aws_config.json` for backend documentation
2. Update `/optimo-frontend/src/aws-config.ts` for frontend use
3. Rebuild and redeploy the frontend