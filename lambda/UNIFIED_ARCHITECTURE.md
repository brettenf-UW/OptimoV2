# Unified Lambda Architecture

## Overview

OptimoV2 has been simplified from 7+ Lambda functions to a single unified handler that manages all API endpoints. This reduces complexity, improves maintainability, and ensures consistent behavior across all operations.

## Architecture

```
Frontend → API Gateway → Unified Lambda Handler → AWS Services
                                    ↓
                         ┌──────────┴──────────┐
                         │                     │
                    AWS Batch              S3 & DynamoDB
                (Optimization Jobs)      (Storage & Metadata)
```

## Single Lambda Handler

The `unified_handler.py` handles all API endpoints:

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/upload` | POST | Generate presigned URL for file upload |
| `/jobs` | POST | Submit new optimization job |
| `/jobs` | GET | List all jobs |
| `/jobs/{jobId}/status` | GET | Get job status |
| `/jobs/{jobId}/results` | GET | Get job results with metrics |
| `/jobs/{jobId}/cancel` | POST | Cancel running job |

## Key Benefits

1. **Simplicity**: One Lambda function instead of 7+
2. **Consistency**: All endpoints use the same status handling
3. **Performance**: Shared code, fewer cold starts
4. **Maintainability**: Fix bugs in one place
5. **Cost**: Fewer Lambda invocations

## Status Handling

The system now uses AWS Batch statuses directly:
- `SUBMITTED` - Job queued
- `PENDING` - Job waiting for resources
- `RUNNABLE` - Job ready to start
- `STARTING` - Job initializing
- `RUNNING` - Job in progress
- `SUCCEEDED` - Job completed successfully
- `FAILED` - Job failed

Frontend utilities handle user-friendly display of these statuses.

## Deployment

1. Deploy the unified handler:
   ```bash
   ./deploy_unified.sh
   ```

2. Update API Gateway routes:
   ```bash
   ./update_api_routes.sh
   ```

3. Test all endpoints work correctly

4. Clean up old Lambda functions:
   ```bash
   ./cleanup_old_lambdas.sh
   ```

## Metrics Calculation

Job results are calculated on-demand when requested:
1. Download CSV files from S3
2. Calculate utilization, teacher load, etc.
3. Cache results in DynamoDB
4. Return metrics with download URLs

This approach ensures metrics are always fresh and reduces storage needs.

## Error Handling

The unified handler includes comprehensive error handling:
- Invalid requests return 400 with clear error messages
- Missing resources return 404
- Server errors return 500 with logged details
- All responses include proper CORS headers

## Future Improvements

1. Add request validation middleware
2. Implement rate limiting
3. Add CloudWatch metrics
4. Consider caching for frequently accessed data
5. Add WebSocket support for real-time updates