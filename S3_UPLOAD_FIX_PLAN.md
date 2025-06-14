# S3 Upload 403 Error Fix Plan

## Problem Summary
The application is getting 403 Forbidden errors when trying to upload files to S3 using presigned URLs generated by Lambda. This is blocking job submission functionality.

## Root Cause Analysis
The issue stems from AWS IAM role temporary credentials and presigned URL complexity:
1. Lambda runs with an IAM role (temporary credentials with session tokens)
2. Presigned URLs generated with temporary credentials have additional security requirements
3. S3 is rejecting uploads due to signature validation failures or permission issues

## Current State
- **Lambda**: Generates presigned URLs with temporary credentials
- **Frontend**: Attempts to upload directly to S3 using these URLs
- **Result**: 403 Forbidden errors on PUT requests

## Solution Options

### Option 1: Base64 Upload Through Lambda (Recommended)
**Approach**: Upload files through Lambda API instead of direct S3 upload
**Pros**: 
- Simpler implementation
- No presigned URL complexity
- Works reliably with Lambda IAM roles
**Cons**: 
- File size limited by Lambda payload (6MB)
- Slightly slower due to base64 encoding

**Implementation**:
1. Modify frontend to send file as base64
2. Update Lambda to receive base64 and upload to S3
3. No AWS permission changes needed

### Option 2: Fix Presigned URL Approach
**Approach**: Properly configure IAM and S3 for presigned URLs
**Pros**: 
- Direct S3 upload (faster for large files)
- No file size limitations
**Cons**: 
- Complex IAM/S3 configuration
- Difficult to debug permission issues

**Troubleshooting Steps**:
1. Check IAM role trust policy
2. Add s3:PutObjectAcl permission
3. Configure S3 bucket policy correctly
4. Handle CORS and signature requirements

### Option 3: Use S3 Transfer Acceleration
**Approach**: Enable S3 Transfer Acceleration for uploads
**Pros**: Faster uploads globally
**Cons**: Additional cost, doesn't solve permission issue

## Recommended Implementation Plan

### Phase 1: Quick Fix (Base64 Upload)
1. **Update Lambda Handler** (`unified_handler.py`):
```python
def handle_upload(event: Dict) -> Dict:
    """Handle file upload via base64"""
    try:
        body = json.loads(event.get('body', '{}'))
        filename = body.get('fileName') or body.get('filename', '')
        file_content = body.get('fileContent', '')  # Base64 encoded
        
        if not filename or not file_content:
            return response(400, {'error': 'Filename and fileContent are required'})
        
        # Generate unique key
        file_id = str(uuid.uuid4())
        file_key = f"uploads/{file_id}/{filename}"
        
        # Decode and upload to S3
        import base64
        file_bytes = base64.b64decode(file_content)
        
        s3.put_object(
            Bucket=INPUT_BUCKET,
            Key=file_key,
            Body=file_bytes,
            ContentType='text/csv'
        )
        
        return response(200, {
            'fileKey': file_key,
            'uploadUrl': f"s3://{INPUT_BUCKET}/{file_key}"  # For reference
        })
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return response(500, {'error': str(e)})
```

2. **Update Frontend** (`api.ts`):
```typescript
// Get presigned URL for file upload
async getUploadUrl(fileName: string, fileType: string): Promise<{uploadUrl: string, fileKey: string}> {
  // Convert file to base64
  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result as string;
        resolve(base64.split(',')[1]); // Remove data:type prefix
      };
      reader.onerror = error => reject(error);
    });
  };
  
  // Note: This needs to be refactored to accept File parameter
  const response = await this.api.post('/upload', { 
    filename: fileName,
    fileContent: await fileToBase64(file) // Need file parameter
  });
  return response.data;
}
```

### Phase 2: Long-term Fix (If Needed)
If file sizes exceed 6MB, implement proper presigned URL configuration:

1. **Create IAM User** with programmatic access for S3 uploads
2. **Store credentials** in AWS Secrets Manager
3. **Update Lambda** to use IAM user credentials for presigned URL generation
4. **Test thoroughly** with different file sizes and types

## Testing Plan
1. Test with small CSV files (<1MB)
2. Test with medium files (1-5MB)
3. Test error handling (invalid files, network errors)
4. Verify job submission works end-to-end

## Rollback Plan
If issues persist:
1. Revert to previous working version
2. Use AWS SDK in frontend with temporary credentials
3. Consider alternative storage solutions

## Timeline
- **Immediate**: Implement base64 upload fix (2-3 hours)
- **Future**: Investigate presigned URL fix if needed (1-2 days)

## Success Criteria
- Files upload successfully without 403 errors
- Job submission completes normally
- No degradation in user experience