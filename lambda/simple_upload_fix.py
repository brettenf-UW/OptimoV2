# Quick fix: Replace presigned URL approach with direct Lambda upload
# This avoids the IAM role/presigned URL complexity

def handle_upload_direct(event: Dict) -> Dict:
    """Direct file upload through Lambda (base64 encoded)"""
    try:
        body = json.loads(event.get('body', '{}'))
        filename = body.get('fileName') or body.get('filename', '')
        file_content = body.get('fileContent', '')  # Base64 encoded
        
        if not filename or not file_content:
            return response(400, {'error': 'Filename and fileContent are required'})
        
        # Generate unique key
        file_id = str(uuid.uuid4())
        file_key = f"uploads/{file_id}/{filename}"
        
        # Decode base64 and upload directly to S3
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
            'message': 'File uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return response(500, {'error': str(e)})