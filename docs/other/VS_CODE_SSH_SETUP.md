# VS Code SSH Remote Connection to Raspberry Pi

## Quick Setup

### 1. Install Remote SSH Extension
- Open VS Code
- Go to Extensions (`Ctrl+Shift+X`)
- Search for "Remote - SSH" by Microsoft
- Click Install

### 2. Add SSH Host

Press `Ctrl+Shift+P` and select **Remote-SSH: Add New SSH Host**

Enter:
```
ssh rhyslwells@192.168.1.215
```

### 3. Connect

Press `Ctrl+Shift+P` and select **Remote-SSH: Connect to Host**

Choose your Pi from the list. VS Code will:
- Install the remote server on your Pi (first time only)
- Open a new window connected to the Pi
- Show you're connected in the bottom-left corner

### 4. Open Workspace

Once connected:
1. Click **File → Open Folder**
2. Navigate to `/home/rhyslwells/RaspPi-Remote-Worker`
3. Click **OK**

## Tips

- **First Connection:** May take a minute as VS Code sets up the remote server
- **SSH Key Auth:** Set up SSH keys on your Pi for password-free connections
- **Keep Connected:** Close the remote terminal cleanly to avoid connection issues
- **Extensions:** Install extensions on the remote side when using them remotely

## Common Commands

```bash
# From the integrated terminal (now on Pi):
git pull origin main
python3 runner.py

# All runs directly on the Pi!
```

## SSH Key Setup (Optional)

For password-free connections:

**On your local machine:**
```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
ssh-copy-id -i ~/.ssh/id_ed25519.pub pi@192.168.1.100
```

Now connections won't require a password.
