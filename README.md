# Falcons Club Security Baseline

Cybersecurity internship project - Ubuntu hardening, Nmap scan and SSH log analysis.  
**Intern:** Alyan Ahsan  
**Client:** Falcons Sports Club  
**Lab:** Ubuntu 22.04.5 LTS on VirtualBox

## Files

```text
configs/
  ssh-settings-verified.txt
  ufw-status-verified.txt
  sudoers-rule-recorded.txt
scripts/
  analyze_logs.py
logs/
  sample_auth.log
  log_analysis_output.txt
  ubuntu-terminal-task1.txt
reports/
  localhost_scan.txt
  task1-hardening.md
  task2-evidence.pdf
evidence/
  task1/1.png ... 9.png
report.md
README.md
```

`report.md` contains the summary, results, remaining risks and recommendations. Config files here are the recorded settings verified in Task 1; they are **not** full exports from the VM.

## How I did the lab

Run commands on your **own Ubuntu lab VM**. Use the Ubuntu administrator account for `sudo`. Keep the VM console available while changing SSH settings.

### 1. Install SSH and UFW

```bash
sudo apt update
sudo apt install -y openssh-server ufw
sudo systemctl enable --now ssh
```

### 2. Create a restricted user

```bash
sudo adduser falconadmin
sudo visudo -f /etc/sudoers.d/falconadmin
```

In the sudoers file, allow only the two UFW status commands shown in `configs/sudoers-rule-recorded.txt`. Check with:

```bash
sudo visudo -c
sudo -l -U falconadmin
```

### 3. Set up SSH key login

In VirtualBox, use NAT forwarding **Windows 127.0.0.1:2222 -> Ubuntu TCP 22**. On **Windows PowerShell**:

```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\falcons_ed25519"
Get-Content "$env:USERPROFILE\.ssh\falcons_ed25519.pub" | ssh -p 2222 falconadmin@127.0.0.1 'umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys'
ssh -p 2222 -i "$env:USERPROFILE\.ssh\falcons_ed25519" -o IdentitiesOnly=yes -o PasswordAuthentication=no falconadmin@127.0.0.1 whoami
```

Confirm key login works **before** turning off password login. Never upload the private SSH key.

### 4. Harden SSH

In Ubuntu:

```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
sudo nano /etc/ssh/sshd_config
```

Set the following active options in the global section, avoiding duplicate directives:

```text
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
```

Then validate and restart:

```bash
sudo sshd -t
sudo sshd -T | grep -E '^(permitrootlogin|passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication) '
sudo systemctl restart ssh
```

Check that SSH key login still works from Windows.

### 5. Configure UFW

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw enable
sudo ufw status verbose
```

### 6. Run a localhost Nmap scan

For this lab, CUPS on port 631 was disabled and an HTTP service was started on port 80:

```bash
sudo systemctl disable --now cups.service cups.socket cups.path
sudo apt install -y nginx nmap
sudo systemctl enable --now nginx
nmap -sT -sV -p- --open -oN localhost_scan.txt 127.0.0.1
```

The recorded scan showed only **22/tcp SSH** and **80/tcp HTTP** open. Save the actual results; do not change them to match an expected output.

### 7. Generate sample SSH failures and analyze logs

This step was done **only on the isolated lab VM**. A temporary SSH configuration backup was made. SSH password authentication was briefly enabled for the controlled test, with root login kept disabled. Three wrong-password attempts were made from Windows PowerShell, then the secure SSH settings were restored and checked again.

```bash
# Ubuntu: back up the current secure SSH configuration before a lab-only test
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.task2.bak
sudo nano /etc/ssh/sshd_config
# Temporarily change PasswordAuthentication to yes, validate with sudo sshd -t,
# verify sudo sshd -T, then sudo systemctl restart ssh.
```

From Windows PowerShell, repeat this command three times and enter an incorrect password each time:

```powershell
ssh -p 2222 -o PubkeyAuthentication=no -o PreferredAuthentications=password -o KbdInteractiveAuthentication=no -o NumberOfPasswordPrompts=1 falconadmin@127.0.0.1
```

Immediately restore the secure configuration **from the Ubuntu VM console**:

```bash
sudo cp /etc/ssh/sshd_config.task2.bak /etc/ssh/sshd_config
sudo sshd -t
sudo systemctl restart ssh
sudo sshd -T | grep -E '^(permitrootlogin|passwordauthentication|kbdinteractiveauthentication) '
```

Confirm `passwordauthentication no` and `permitrootlogin no` before continuing. Collect only actual failed SSH log entries, not the unrelated `sudo grep` lines:

```bash
sudo grep -aE 'sshd\[[0-9]+\]: Failed password for ' /var/log/auth.log | tail -n 3 > sample_auth.log
```

Copy the sample log into `logs/` and run the original script from the directory containing that log:

```bash
cd logs
python3 ../scripts/analyze_logs.py
python3 ../scripts/analyze_logs.py > log_analysis_output.txt
```

The script prints lines containing `Failed password`. The original 3-line sample and output are provided in `logs/`.

## Notes

- Do not use a private SSH key, real member data, or full unreviewed authentication logs in a public GitHub repository.
- The localhost scan does not prove external network exposure.
- Before using a real server, apply security updates, configure HTTPS, arrange backups and enable ongoing monitoring.
