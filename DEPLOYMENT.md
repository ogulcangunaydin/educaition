# GitHub Actions Deployment Setup Guide

This guide explains how to set up automated deployments using GitHub Actions for the educaition project.

## Prerequisites

- Lightsail Instance: `educaition`
- AWS Region: `eu-central-1` (Frankfurt)
- Server IP: `63.179.49.61`
- SSH User: `ubuntu`

---

## Step 1: Create AWS IAM User

### 1.1 Create IAM Policy

1. Go to: https://console.aws.amazon.com/iam/home#/policies
2. Click **Create policy**
3. Select **JSON** tab and paste:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LightsailSSHAccess",
            "Effect": "Allow",
            "Action": [
                "lightsail:OpenInstancePublicPorts",
                "lightsail:CloseInstancePublicPorts",
                "lightsail:GetInstance"
            ],
            "Resource": "*"
        }
    ]
}
```

4. Click **Next**
5. Name it: `LightsailSSHManagement`
6. Click **Create policy**

### 1.2 Create IAM User

1. Go to: https://console.aws.amazon.com/iam/home#/users
2. Click **Create user**
3. Name: `github-actions-deploy`
4. Click **Next**
5. Select **Attach policies directly**
6. Search and select `LightsailSSHManagement`
7. Click **Next** → **Create user**

### 1.3 Create Access Keys

1. Click on user `github-actions-deploy`
2. Go to **Security credentials** tab
3. Click **Create access key**
4. Select **Application running outside AWS**
5. Click **Create access key**
6. **⚠️ COPY BOTH KEYS NOW** (you won't see them again!)

---

## Step 2: Get SSH Private Key

Your SSH key is located at:
```
~/Downloads/LightsailDefaultKey-eu-central-1.pem
```

View and copy it:
```bash
cat ~/Downloads/LightsailDefaultKey-eu-central-1.pem
```

Copy the **entire content** including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`

---

## Step 3: Add GitHub Secrets

### For educaition-react (Frontend)

Go to: https://github.com/ogulcangunaydin/educaition-react/settings/secrets/actions

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `SSH_PRIVATE_KEY` | Content of `LightsailDefaultKey-eu-central-1.pem` |
| `AWS_ACCESS_KEY_ID` | Your AWS access key (from Step 1.3) |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key (from Step 1.3) |
| `VITE_API_BASE_URL` | `https://api.educaition.net.tr` |

Optional (for Cloudflare cache purge):
| `CLOUDFLARE_ZONE_ID` | Your Cloudflare zone ID |
| `CLOUDFLARE_API_TOKEN` | Your Cloudflare API token |

### For educaition (Backend)

Go to: https://github.com/ogulcangunaydin/educaition/settings/secrets/actions

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `SSH_PRIVATE_KEY` | Content of `LightsailDefaultKey-eu-central-1.pem` |
| `AWS_ACCESS_KEY_ID` | Your AWS access key (from Step 1.3) |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key (from Step 1.3) |

---

## Step 4: Push Workflow Files

### Frontend
```bash
cd ~/Projects/educaition-react
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions deployment workflow"
git push origin master
```

### Backend
```bash
cd ~/Projects/educaition
git add .github/workflows/deploy.yml DEPLOYMENT.md
git commit -m "Add GitHub Actions deployment workflow"
git push origin main
```

---

## How It Works

### Security
- GitHub Actions runner gets a temporary IP
- Opens Lightsail firewall for that IP only
- Deploys via SSH
- **Closes the firewall** after deployment (even if it fails)
- Your SSH port stays closed to the public!

### Automatic Deployment
- **Frontend**: Deploys on every push to `master`
- **Backend**: Deploys on every push to `master` or `main`

### Manual Deployment
1. Go to repository → **Actions** tab
2. Select the workflow
3. Click **Run workflow** → **Run workflow**

---

## Deployment Paths

| Component | Server Path |
|-----------|-------------|
| Frontend | `/srv/app/frontend/build` |
| Backend | `/srv/app/educaition` |

---

## Troubleshooting

### SSH Connection Failed
- Check that `SSH_PRIVATE_KEY` includes the full key with headers
- Verify AWS credentials are correct

### Migration Failed
```bash
ssh -i ~/Downloads/LightsailDefaultKey-eu-central-1.pem ubuntu@63.179.49.61
cd /srv/app/educaition
python3.10 -m alembic current
python3.10 -m alembic history
```

### Firewall Not Opening
- Verify Lightsail instance name is `educaition`
- Check IAM policy is attached to the user
