# django-ftp

Python: 3.14

## Local Development

Start Django server:

```bash
python manage.py runserver [addr:port]
```

Start the FTP server:

```bash
python manage.py ftpserver [addr:port]
```

## Production Deployment on CentOS Server

### 1. Server Setup

Update system and install required packages:

```bash
# Update system
sudo yum update -y

# Install Python 3 and pip
sudo yum install python3 python3-pip python3-devel -y

# Install git
sudo yum install git -y

# Install build dependencies
sudo yum install gcc openssl-devel bzip2-devel libffi-devel -y
```

### 2. Deploy Your Application

```bash
# Clone your repository
cd /opt
sudo git clone https://github.com/shahedpy/django-ftp.git
cd django-ftp

# Create virtual environment
sudo python3 -m venv venv
sudo chown -R $USER:$USER venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up local_settings.py
sudo cp examples/local_settings.example CONFIG/local_settings.py
sudo nano CONFIG/local_settings.py  # Update with your AWS credentials
```

### 3. Configure Firewall

Open the FTP port to allow external connections:

```bash
# Open FTP port (default 2121)
sudo firewall-cmd --permanent --add-port=2121/tcp
sudo firewall-cmd --reload

# If using standard FTP port 21 (requires root privileges)
# sudo firewall-cmd --permanent --add-port=21/tcp
# sudo firewall-cmd --reload
```

### 4. Create Systemd Service

Create a systemd service file at `/etc/systemd/system/django-ftp.service`:

```ini
[Unit]
Description=Django FTP Server
After=network.target

[Service]
Type=simple
User=<your-username>
WorkingDirectory=/opt/django-ftp
Environment="PATH=/opt/django-ftp/venv/bin"
ExecStart=/opt/django-ftp/venv/bin/python /opt/django-ftp/manage.py ftpserver 0.0.0.0:2121
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Create the service file
sudo nano /etc/systemd/system/django-ftp.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable django-ftp

# Start the service
sudo systemctl start django-ftp

# Check status
sudo systemctl status django-ftp
```

### 5. Update Django Settings

Update `CONFIG/settings.py` for production:

```python
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['your-server-ip', 'your-domain.com']
```

### 6. Set Up Logging

Create log directory:

```bash
sudo mkdir -p /var/log/django-ftp
sudo chown -R <your-username>:<your-username> /var/log/django-ftp
```

Add logging configuration to `CONFIG/settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django-ftp/django-ftp.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'CONFIG.filesystems': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### 7. Security Considerations

**Important security updates for production:**

1. **Change SECRET_KEY**: Generate a new secret key in `CONFIG/settings.py`
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **Use Environment Variables**: Update `CONFIG/settings.py` to use environment variables for sensitive data:
   ```python
   import os
   
   SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'your-secret-key-here')
   
   # At the end of settings.py
   try:
       from .local_settings import *
   except ImportError:
       # Fall back to environment variables
       AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
       AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
       AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
       AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'ap-southeast-1')
       AWS_LOCATION = os.environ.get('AWS_LOCATION', 'sw_data')
   ```

3. **Never commit `CONFIG/local_settings.py`** with real credentials to version control

4. **Set strong FTP user passwords** in your user management system

### 8. Monitor and Manage

Useful commands for managing the service:

```bash
# View real-time logs
sudo journalctl -u django-ftp -f

# View recent logs
sudo journalctl -u django-ftp -n 100

# Restart service
sudo systemctl restart django-ftp

# Stop service
sudo systemctl stop django-ftp

# Check service status
sudo systemctl status django-ftp
```

### 9. Optional: Use Nginx as Reverse Proxy

If you want to expose the Django web interface through HTTP/HTTPS:

```bash
# Install Nginx
sudo yum install nginx -y

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Open HTTP/HTTPS ports
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

Create Nginx configuration at `/etc/nginx/conf.d/django-ftp.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/django-ftp/static/;
    }

    location /media/ {
        alias /opt/django-ftp/media/;
    }
}
```

Then restart Nginx:

```bash
sudo systemctl restart nginx
```

## Connecting to the FTP Server

Use any FTP client to connect:

```
Host: your-server-ip
Port: 2121 (or 21 if you changed it)
Username: <your-ftp-username>
Password: <your-ftp-password>
```

Command line example:

```bash
ftp your-server-ip 2121
```