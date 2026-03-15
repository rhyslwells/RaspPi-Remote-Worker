Explain this script



# What the setup.sh does

```bash
#!/bin/bash                    # Tells system this is a bash script

set -e                         # Exit if any command fails
cd ~/RaspPi-Remote-Worker      # Navigate to directory

# Run commands sequentially
echo "Installing packages..."  # Print message
sudo apt update                # Execute command
sudo apt install -y python3    # -y means "yes to all prompts"

# Check if file exists
if [ -f "credentials.json" ]; then
    echo "Found credentials"
fi
```

### setup.sh (Automated Installation)

**What it does:**
- Updates system packages
- Installs Python 3.10+, git, build tools
- Installs UV package manager
- Clones the repository
- Creates virtual environment
- Installs Python dependencies
- Sets up systemd service for auto-start

**How to run:**
```bash
# On the Raspberry Pi (via SSH)
curl -sSL https://raw.githubusercontent.com/rhyslwells/RaspPi-Remote-Worker/main/setup.sh | bash

# Or manually:
cd ~ && bash ~/RaspPi-Remote-Worker/setup.sh
```

**Duration:** ~10 minutes (depending on system speed and internet)

**Benefits of this approach:**
- ✅ No manual typing = fewer errors
- ✅ Reproducible setup
- ✅ Good for learning what each step does (read the script!)

---

### 3. **Run Automated Setup on Pi**

Once connected to your Pi via SSH:
```bash
curl -sSL https://raw.githubusercontent.com/rhyslwells/RaspPi-Remote-Worker/main/setup.sh | bash
```

This runs `setup.sh` which automates all installation steps.





