# Task 1 - Server Hardening

**Name:** Alyan Ahsan  
**VM:** `falcons-server`  
**OS:** Ubuntu 22.04.5 LTS  
**Tools:** VirtualBox, OpenSSH, UFW, Windows PowerShell

I used Ubuntu Terminal for server commands and Windows PowerShell to connect to the VM. The outputs below are from my own terminal logs. Long installation output and repeated login banners are shortened; the original Ubuntu transcript is in `../logs/ubuntu-terminal-task1.txt`.

## 1. Install SSH and UFW

**Ubuntu Terminal**

```bash
sudo apt update
```

```text
Hit:1 http://security.ubuntu.com/ubuntu jammy-security InRelease
Hit:2 http://pk.archive.ubuntu.com/ubuntu jammy InRelease
Hit:3 http://pk.archive.ubuntu.com/ubuntu jammy-updates InRelease
Hit:4 http://pk.archive.ubuntu.com/ubuntu jammy-backports InRelease
Reading package lists... Done
464 packages can be upgraded. Run 'apt list --upgradable' to see them.
```

```bash
sudo apt install -y openssh-server ufw
```

```text
ufw is already the newest version (0.36.1-4ubuntu0.1).
Setting up openssh-server (1:8.9p1-3ubuntu0.18) ...
Setting up openssh-sftp-server (1:8.9p1-3ubuntu0.18) ...
```

```bash
sudo systemctl enable --now ssh
sudo systemctl status ssh
```

```text
ssh.service - OpenBSD Secure Shell server
Loaded: loaded (/lib/systemd/system/ssh.service; enabled; vendor preset: enabled)
Active: active (running)
Server listening on 0.0.0.0 port 22.
Server listening on :: port 22.
```

```bash
ssh -V
sudo ufw version
sudo systemctl is-active ssh
```

```text
OpenSSH_8.9p1 Ubuntu-3ubuntu0.18, OpenSSL 3.0.2 15 Mar 2022
ufw 0.36.1
active
```

## 2. Create a non-root user

**Ubuntu Terminal**

```bash
sudo adduser falconadmin
```

```text
Adding new group `falconadmin' (1001) ...
Adding new user `falconadmin' (1001) with group `falconadmin' ...
Creating home directory `/home/falconadmin' ...
passwd: password updated successfully
```

The initial password attempts showed password-strength and mismatch warnings. The user was eventually created. I still need to confirm that the account password has been changed to a strong one.

```bash
id falconadmin
getent passwd falconadmin
command -v ufw
```

```text
uid=1001(falconadmin) gid=1001(falconadmin) groups=1001(falconadmin)
falconadmin:x:1001:1001:Falcon Admin,,,:/home/falconadmin:/bin/bash
/usr/sbin/ufw
```

### Limited sudo access

```bash
sudo visudo -f /etc/sudoers.d/falconadmin
```

I added this rule to the file:

```text
falconadmin ALL=(root) /usr/sbin/ufw status, /usr/sbin/ufw status verbose
```

```bash
sudo visudo -c
sudo -l -U falconadmin
```

```text
/etc/sudoers: parsed OK
/etc/sudoers.d/README: parsed OK
/etc/sudoers.d/falconadmin: parsed OK

User falconadmin may run the following commands on falcons-server:
    (root) /usr/sbin/ufw status, /usr/sbin/ufw status verbose
```

This allows `falconadmin` to **view** the UFW firewall status with sudo, without granting unrestricted sudo privileges.

## 3. Set up SSH keys and test login

**Windows PowerShell** - the VirtualBox port-forwarding rule maps Windows `127.0.0.1:2222` to Ubuntu TCP `22`.

```powershell
ssh -p 2222 alyan@127.0.0.1
```

The first attempt returned:

```text
ssh: connect to host 127.0.0.1 port 2222: Connection refused
```

After the port-forwarding rule was saved, this command connected and the user was confirmed:

```text
alyan@falcons-server:~$ whoami
alyan
```

Before hardening, I also verified that the new account could sign in using its Ubuntu password:

```powershell
ssh -p 2222 falconadmin@127.0.0.1
```

```text
falconadmin@falcons-server:~$
```

I then exited the SSH session before running the following commands on Windows:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh"
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\falcons_ed25519"
```

```text
Directory: C:\Users\alyan
Name: .ssh
Your identification has been saved in C:\Users\alyan\.ssh\falcons_ed25519
Your public key has been saved in C:\Users\alyan\.ssh\falcons_ed25519.pub
```

Installed the **public key** in `falconadmin`'s `authorized_keys`:

```powershell
Get-Content "$env:USERPROFILE\.ssh\falcons_ed25519.pub" | ssh -p 2222 falconadmin@127.0.0.1 'umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys'
```

```text
falconadmin@127.0.0.1's password:
# No further terminal output; command returned to PowerShell.
```

The private key remained on Windows and was **not** added to this repository.

Key-only login test:

```powershell
ssh -p 2222 -i "$env:USERPROFILE\.ssh\falcons_ed25519" -o IdentitiesOnly=yes -o PreferredAuthentications=publickey -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no falconadmin@127.0.0.1 whoami
```

```text
Enter passphrase for key 'C:\Users\alyan\.ssh\falcons_ed25519':
falconadmin
```

## 4. Change SSH settings

**Ubuntu Terminal** (as `alyan`, which has normal administrator access)

```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
sudo nano /etc/ssh/sshd_config
```

Settings entered in the file:

```text
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
```

Syntax check:

```bash
sudo sshd -t
```

```text
(no output; syntax check passed)
```

Effective settings check:

```bash
sudo sshd -T | grep -E '^(permitrootlogin|passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication) '
```

```text
permitrootlogin no
pubkeyauthentication yes
passwordauthentication no
kbdinteractiveauthentication no
```

Restart and check the service:

```bash
sudo systemctl restart ssh
sudo systemctl is-active ssh
```

```text
active
```

### Check blocked logins

**Windows PowerShell** - attempt to use a password instead of a key:

```powershell
ssh -p 2222 -o PreferredAuthentications=password -o PubkeyAuthentication=no -o KbdInteractiveAuthentication=no falconadmin@127.0.0.1
```

```text
falconadmin@127.0.0.1: Permission denied (publickey).
```

**Windows PowerShell** - attempt to connect as `root`:

```powershell
ssh -p 2222 -i "$env:USERPROFILE\.ssh\falcons_ed25519" -o IdentitiesOnly=yes root@127.0.0.1
```

```text
root@127.0.0.1: Permission denied (publickey).
```

**Ubuntu Terminal** - confirm root password state:

```bash
sudo passwd -S root
```

```text
root L 11/14/2026 0 99999 7 -1
```

`L` indicates that the root password was locked.

## 5. Set up UFW firewall

**Ubuntu Terminal**

```bash
sudo ufw default deny incoming
```

```text
Default incoming policy changed to 'deny'
(be sure to update your rules accordingly)
```

```bash
sudo ufw default allow outgoing
```

```text
Default outgoing policy changed to 'allow'
(be sure to update your rules accordingly)
```

```bash
sudo ufw allow 22/tcp
```

```text
Rules updated
Rules updated (v6)
```

```bash
sudo ufw allow 80/tcp
```

```text
Rules updated
Rules updated (v6)
```

```bash
sudo ufw show added
```

```text
Added user rules (see 'ufw status' for running firewall):
ufw allow 22/tcp
ufw allow 80/tcp
```

```bash
sudo ufw enable
```

```text
Firewall is active and enabled on system startup
```

```bash
sudo ufw status verbose
```

```text
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere
80/tcp                     ALLOW IN    Anywhere
22/tcp (v6)                ALLOW IN    Anywhere (v6)
80/tcp (v6)                ALLOW IN    Anywhere (v6)
```

The extra `(v6)` lines are the same two permitted ports for IPv6. Other incoming ports are denied by the default policy.

## 6. Check SSH again after enabling UFW

**Windows PowerShell**

```powershell
ssh -p 2222 -i "$env:USERPROFILE\.ssh\falcons_ed25519" -o IdentitiesOnly=yes -o PasswordAuthentication=no falconadmin@127.0.0.1 whoami
```

```text
Enter passphrase for key 'C:\Users\alyan\.ssh\falcons_ed25519':
falconadmin
```

So UFW did not block the permitted SSH connection.

## 7. Issues I fixed during the lab

- **Connection refused:** Initial SSH connection failed before the VirtualBox NAT forwarding rule was saved. The same SSH command later worked.
- **PowerShell command in Ubuntu:** I accidentally ran `Get-Content` on Ubuntu. It returned `Get-Content: command not found`; I reran it from Windows PowerShell.
- **Linux command in Windows:** I ran `sudo passwd -S root` in PowerShell. Windows returned `Sudo is disabled on this machine`. The check worked when run in Ubuntu.
- **Wrong SSH test terminal:** A Windows-style SSH command was also run in Ubuntu. It reported that the Windows key path was unavailable, so I reran the test from Windows.

## 8. Final checklist

| Requirement | Result |
|---|---|
| Non-root user `falconadmin` exists | Verified (`id falconadmin`) |
| Limited sudo access | Verified (`sudo -l -U falconadmin`) |
| SSH key login | Verified (`whoami` returned `falconadmin`) |
| SSH password login disabled | Verified (denied) |
| Root SSH login disabled | Verified (denied) |
| Root password locked | Verified (`root L`) |
| Effective SSH configuration | Verified (`sshd -T`) |
| UFW allows only TCP 22 and 80 | Verified (`ufw status verbose`) |
| SSH still works after UFW | Verified |
| Direct contents of `/etc/ssh/sshd_config` | **Output not yet captured** |
| Initial VM snapshot | **Not verified from provided evidence** |
| Strong `falconadmin` password | **Change/confirmation pending** |

## 9. Add before submitting

The supervisor specifically wants evidence from the actual SSH configuration **file**, not just `sshd -T`. Run this in Ubuntu and paste the output here:

```bash
sudo grep -nE '^[[:space:]]*(PermitRootLogin|PasswordAuthentication|KbdInteractiveAuthentication|PubkeyAuthentication)[[:space:]]' /etc/ssh/sshd_config
```

```text
[PASTE ACTUAL OUTPUT HERE]
```

Also confirm the `Before-Hardening` VM snapshot. If the `falconadmin` account still has the weak password, change it from Ubuntu with `sudo passwd falconadmin` and do not include the password in this file.

**Note:** `apt update` found hundreds of pending packages. This report does not claim they have been installed. Installing security updates is recommended for a real server, but the Task 1 mentor checklist does not explicitly ask for patch completion.
