# 🚀 COMPLETE GUIDE: S3 Setup + Integration with FastAPI APIs

> For: **Uploading processed images to AWS S3** and returning **signed URLs**  
> When: You receive **AWS access credentials**

---

## ✅ PHASE 1: AWS SETUP (from scratch)

### 🔹 1. Create AWS Account (if not done yet)
- Go to [https://aws.amazon.com](https://aws.amazon.com)
- Create account → Choose **Free Tier** or as per your usage
- Complete email verification, password, and payment info.

### 🔹 2. Go to AWS Management Console
- Login → Search and open **IAM (Identity and Access Management)**

### 🔹 3. Create an IAM User
1. In IAM dashboard → Users → **Create User**
2. Enter a name like: `immerso-s3-user`
3. Enable **Programmatic access**
4. **Permissions → Attach policies directly**
5. Attach:
   - `AmazonS3FullAccess` (for now; use limited scope in future)
6. Click **Create User**
7. ✅ You'll get:
   - `Access Key ID`
   - `Secret Access Key`

### 🔹 4. Create S3 Bucket
1. Search “S3” in AWS Console
2. Click “Create Bucket”
   - **Bucket name:** `immerso-bg-change`
   - **Region:** e.g. `Asia Pacific (Mumbai) ap-south-1`
3. Uncheck **Block all public access** (for signed URL to work)
4. Click **Create Bucket**

---

## ✅ PHASE 2: Store AWS Keys Locally in `.env`

Create a `.env` file in your FastAPI root folder:

```env
AWS_ACCESS_KEY_ID=AKIAEXAMPLEKEY
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=ap-south-1
S3_BUCKET_NAME=immerso-bg-change
```

Install dotenv:
```bash
pip install python-dotenv
```

In `main.py`, at the top:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## ✅ PHASE 3: Install and Set Up `boto3`
```bash
pip install boto3
```

---

## ✅ PHASE 4: Create `upload_to_s3.py`

```python
import boto3, os
from botocore.exceptions import NoCredentialsError

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def upload_file_to_s3(local_file_path, s3_key):
    try:
        s3.upload_file(local_file_path, os.getenv("S3_BUCKET_NAME"), s3_key)
        return True
    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")
    return False

def generate_presigned_url(s3_key, expires_in=3600):
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': os.getenv("S3_BUCKET_NAME"), 'Key': s3_key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as e:
        print(f"Error generating signed URL: {str(e)}")
        return None
```

---

## ✅ PHASE 5: Modify `main.py` (Where & What)

### 1. At the top of `main.py`, after `import os`, add:

```python
from dotenv import load_dotenv
load_dotenv()

from upload_to_s3 import upload_file_to_s3, generate_presigned_url
```

### 2. Inside `background_change()` — AFTER this line:

```python
output_path = f"{RESULTS_DIR}/result_{gen_id}_0.png"
```

Add this block after inpainting:

```python
# Upload output to S3
s3_key = f"results/{os.path.basename(output_path)}"
upload_success = upload_file_to_s3(output_path, s3_key)

if upload_success:
    signed_url = generate_presigned_url(s3_key)
else:
    signed_url = None
```

### 3. In the `generation_status[gen_id] = { ... }` block, add:

```python
"signed_url": signed_url,
```

### 4. In `/backgroundchange/status/{generation_id}` → replace:

```python
"signed_result_url": f"{BASE_SIGNED_URL}/{os.path.basename(data['output'])}"
```

With:

```python
"signed_result_url": data.get("signed_url")
```

---

## ✅ PHASE 6: Test Full Flow

### Test 1: Background Change
```bash
curl --location 'http://localhost:8003/background-change' \\
--form 'image=@"test.jpg"' \\
--form 'prompt="sunset city"' \\
--form 'user_id="1234"'
```

### Test 2: Check Status
```bash
curl http://localhost:8003/backgroundchange/status/<generation_id>
```

---

## ✅ PHASE 7: (Optional) Cleanup Local Files

```python
import os
try:
    os.remove(output_path)
    os.remove(input_path)
    os.remove(mask_path)
except Exception as e:
    print(f"Cleanup error: {str(e)}")
```

