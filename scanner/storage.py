"""AWS S3 and DynamoDB storage integration for DevGuard."""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class S3Storage:
    """S3 storage for scan reports."""
    
    def __init__(self, bucket_name: Optional[str] = None, region: str = 'us-east-1'):
        """
        Initialize S3 storage.
        
        Args:
            bucket_name: S3 bucket name. If None, reads from env var DEVGUARD_S3_BUCKET
            region: AWS region (default: us-east-1)
        """
        self.bucket_name = bucket_name or os.environ.get('DEVGUARD_S3_BUCKET')
        self.region = region or os.environ.get('AWS_REGION', 'us-east-1')
        
        if self.bucket_name:
            try:
                self.s3_client = boto3.client('s3', region_name=self.region)
                # Test connection
                self.s3_client.head_bucket(Bucket=self.bucket_name)
            except NoCredentialsError:
                # If no credentials, S3 operations will fail gracefully
                self.s3_client = None
                # Silently fail - don't print in production
                pass
            except ClientError as e:
                error_code = e.response['Error']['Code']
                self.s3_client = None
                # Silently fail - don't print in production
                pass
        else:
            self.s3_client = None
    
    def upload_report(self, findings: List[Dict], report_id: Optional[str] = None) -> Optional[str]:
        """
        Upload scan report to S3.
        
        Args:
            findings: List of finding dictionaries
            report_id: Optional report ID. If None, generates timestamp-based ID
            
        Returns:
            S3 key (path) if successful, None otherwise
        """
        if not self.s3_client or not self.bucket_name:
            return None
        
        if not findings:
            return None
        
        # Generate report ID if not provided
        if not report_id:
            report_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # S3 key: reports/YYYY/MM/DD/report_YYYYMMDD_HHMMSS.json
        date_path = datetime.now().strftime('%Y/%m/%d')
        s3_key = f"reports/{date_path}/report_{report_id}.json"
        
        try:
            # Prepare report data
            report_data = {
                'report_id': report_id,
                'timestamp': datetime.now().isoformat(),
                'total_findings': len(findings),
                'findings': findings
            }
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(report_data, indent=2),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            return s3_key
            
        except ClientError as e:
            print(f"❌ Error uploading to S3: {e}")
            return None
    
    def upload_csv_report(self, csv_content: str, report_id: Optional[str] = None) -> Optional[str]:
        """
        Upload CSV report to S3.
        
        Args:
            csv_content: CSV file content as string
            report_id: Optional report ID. If None, generates timestamp-based ID
            
        Returns:
            S3 key (path) if successful, None otherwise
        """
        if not self.s3_client or not self.bucket_name:
            return None
        
        if not csv_content:
            return None
        
        # Generate report ID if not provided
        if not report_id:
            report_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # S3 key: reports/YYYY/MM/DD/report_YYYYMMDD_HHMMSS.csv
        date_path = datetime.now().strftime('%Y/%m/%d')
        s3_key = f"reports/{date_path}/report_{report_id}.csv"
        
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=csv_content.encode('utf-8'),
                ContentType='text/csv',
                ServerSideEncryption='AES256'
            )
            
            return s3_key
            
        except ClientError as e:
            print(f"❌ Error uploading CSV to S3: {e}")
            return None
    
    def get_report_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for report download.
        
        Args:
            s3_key: S3 key (path) of the report
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL if successful, None otherwise
        """
        if not self.s3_client or not self.bucket_name:
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            print(f"❌ Error generating presigned URL: {e}")
            return None


class DynamoDBStorage:
    """DynamoDB storage for scan history and user data (future use)."""
    
    def __init__(self, table_name: Optional[str] = None, region: str = 'us-east-1'):
        """
        Initialize DynamoDB storage.
        
        Args:
            table_name: DynamoDB table name. If None, reads from env var DEVGUARD_DYNAMODB_TABLE
            region: AWS region (default: us-east-1)
        """
        self.table_name = table_name or os.environ.get('DEVGUARD_DYNAMODB_TABLE')
        self.region = region or os.environ.get('AWS_REGION', 'us-east-1')
        
        if self.table_name:
            try:
                self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
                self.table = self.dynamodb.Table(self.table_name)
                # Test connection
                self.table.meta.client.describe_table(TableName=self.table_name)
            except NoCredentialsError:
                self.table = None
                # Silently fail - don't print in production
                pass
            except ClientError as e:
                error_code = e.response['Error']['Code']
                self.table = None
                # Silently fail - don't print in production
                pass
        else:
            self.table = None
    
    def save_scan(self, user_id: str, scan_id: str, findings: List[Dict], 
                  metadata: Optional[Dict] = None, s3_key: Optional[str] = None) -> bool:
        """
        Save scan results to DynamoDB.
        
        Args:
            user_id: User identifier
            scan_id: Unique scan ID
            findings: List of finding dictionaries
            metadata: Optional metadata (file names, scan duration, etc.)
            s3_key: Optional S3 key where report is stored
            
        Returns:
            True if successful, False otherwise
        """
        if not self.table:
            return False
        
        try:
            item = {
                'user_id': user_id,
                'scan_id': scan_id,
                'timestamp': datetime.now().isoformat(),
                'total_findings': len(findings),
                'findings': json.dumps(findings),
                'ttl': int((datetime.now().timestamp() + (90 * 24 * 60 * 60)))  # 90 days TTL
            }
            
            if metadata:
                item['metadata'] = json.dumps(metadata)
            
            if s3_key:
                item['s3_key'] = s3_key
            
            self.table.put_item(Item=item)
            return True
            
        except ClientError as e:
            # Silently fail - error will be logged by caller
            return False
    
    def get_user_scans(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get recent scans for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of scans to return
            
        Returns:
            List of scan dictionaries
        """
        if not self.table:
            return []
        
        try:
            response = self.table.query(
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id},
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            scans = []
            for item in response.get('Items', []):
                scan = {
                    'scan_id': item.get('scan_id'),
                    'timestamp': item.get('timestamp'),
                    'total_findings': item.get('total_findings', 0),
                    'findings': json.loads(item.get('findings', '[]'))
                }
                if 'metadata' in item:
                    scan['metadata'] = json.loads(item['metadata'])
                scans.append(scan)
            
            return scans
            
        except ClientError as e:
            print(f"❌ Error querying DynamoDB: {e}")
            return []

