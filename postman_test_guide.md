# Testing OptimoV2 API with Postman

This guide will walk you through testing the OptimoV2 API using Postman to simulate a job submission with 3 iterations and default utilization range.

## Prerequisites

1. Install [Postman](https://www.postman.com/downloads/)
2. Have access to the CSV files in `/mnt/c/dev/OptimoV2/data/runs/run_20250610_010706/iterations/iter_0/input/`

## Step 1: Test the Upload Endpoint

First, we need to upload each CSV file to S3 using the upload endpoint.

### Request Details

- **Method**: POST
- **URL**: `https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod/upload`
- **Headers**:
  - `Content-Type`: `application/json`
  - `Origin`: `https://brettenf-uw.github.io`
- **Body** (for Period.csv):
```json
{
  "fileName": "Period.csv",
  "fileType": "text/csv"
}
```

### Expected Response

```json
{
  "uploadUrl": "https://optimo-input-files.s3.us-west-2.amazonaws.com/uploads/...",
  "fileKey": "uploads/YYYYMMDDHHMMSS-Period.csv"
}
```

### Upload the File

1. Copy the `uploadUrl` from the response
2. Open a new request in Postman
3. Set the method to PUT
4. Paste the `uploadUrl` as the request URL
5. Set the header `Content-Type` to `text/csv`
6. In the Body tab, select "binary" and upload the Period.csv file
7. Send the request

### Repeat for Each CSV File

Repeat the above steps for each of the following files:
- `Period.csv`
- `Sections_Information.csv`
- `Student_Info.csv`
- `Student_Preference_Info.csv`
- `Teacher_Info.csv`
- `Teacher_unavailability.csv`

Keep track of the `fileKey` values returned for each file, as you'll need them for the job submission.

## Step 2: Submit a Job

After uploading all CSV files, submit a job to process them.

### Request Details

- **Method**: POST
- **URL**: `https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod/jobs`
- **Headers**:
  - `Content-Type`: `application/json`
  - `Origin`: `https://brettenf-uw.github.io`
- **Body**:
```json
{
  "files": [
    "fileKey1",
    "fileKey2",
    "fileKey3",
    "fileKey4",
    "fileKey5",
    "fileKey6"
  ],
  "parameters": {
    "iterations": 3,
    "minUtilization": 75,
    "maxUtilization": 115
  }
}
```

Replace `fileKey1`, `fileKey2`, etc. with the actual file keys returned from the upload requests.

### Expected Response

```json
{
  "jobId": "uuid-string",
  "status": "SUBMITTED",
  "position": 0,
  "submittedAt": 1749575000
}
```

## Step 3: Check Job Status

Use the job ID from the previous response to check the status of the job.

### Request Details

- **Method**: GET
- **URL**: `https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod/jobs/{jobId}/status`
- **Headers**:
  - `Origin`: `https://brettenf-uw.github.io`

Replace `{jobId}` with the actual job ID from the submission response.

### Expected Response

```json
{
  "jobId": "uuid-string",
  "status": "RUNNING",
  "submittedAt": 1749575000,
  "statusReason": ""
}
```

The status will initially be "SUBMITTED" or "RUNNING" and eventually change to "SUCCEEDED" when the job completes.

## Step 4: Get Job Results

Once the job status is "SUCCEEDED", you can retrieve the results.

### Request Details

- **Method**: GET
- **URL**: `https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod/jobs/{jobId}/results`
- **Headers**:
  - `Origin`: `https://brettenf-uw.github.io`

Replace `{jobId}` with the actual job ID.

### Expected Response

```json
{
  "jobId": "uuid-string",
  "status": "SUCCEEDED",
  "downloadUrls": {
    "Master_Schedule.csv": "https://optimo-output-files.s3.us-west-2.amazonaws.com/...",
    "Student_Assignments.csv": "https://optimo-output-files.s3.us-west-2.amazonaws.com/...",
    "Teacher_Schedule.csv": "https://optimo-output-files.s3.us-west-2.amazonaws.com/...",
    "Constraint_Violations.csv": "https://optimo-output-files.s3.us-west-2.amazonaws.com/..."
  },
  "metrics": {
    "summary": {
      "overallUtilization": 85.5,
      "sectionsOptimized": 120,
      "studentsPlaced": 98.2,
      "averageTeacherLoad": 5.3,
      "violations": 2
    },
    "charts": {
      "utilizationDistribution": [5, 10, 50, 60, 5],
      "teacherLoadDistribution": [2, 10, 15, 3, 0]
    },
    "optimizationSummary": "Section utilization is optimal at 85.5%. 92.3% of sections are within the optimal utilization range. 98.2% of students were successfully placed. Teacher load is balanced at 5.3 sections per teacher. There are 2 constraint violations that need attention."
  }
}
```

## Troubleshooting

If you encounter any errors during testing, check the following:

1. **CORS Headers**: Verify that the response includes the `Access-Control-Allow-Origin` header with the value `https://brettenf-uw.github.io`.

2. **Status Codes**: 
   - 200: Success
   - 400: Bad request (check your request body)
   - 403: Forbidden (check permissions)
   - 404: Not found (check URL)
   - 502: Bad Gateway (server error)

3. **Request Format**: Ensure your request body is properly formatted JSON.

4. **File Types**: Make sure the file types match what the server expects.

## Comparing Old vs New API

If you want to compare the old API with the new one, simply replace the base URL:

- Old API: `https://ppwbzsy1bh.execute-api.us-west-2.amazonaws.com/prod`
- New API: `https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod`

This will help identify if the issues are specific to one API or affect both.
