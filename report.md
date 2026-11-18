# Falcons Club Security Baseline - Final Report

**Client:** Falcons Sports Club  
**Intern:** Alyan Ahsan  
**Environment:** Ubuntu 22.04.5 LTS on VirtualBox  
**Project:** Lab Hardening and Recon (Tasks 1-3)  
**Evidence collected:** 14-16 November 2026

## 1. Summary

I set up a security baseline on the club's lab Ubuntu machine. I secured SSH access, limited sudo permissions for a new user and enabled the UFW firewall. I then scanned localhost with Nmap and checked SSH login logs using a Python script. This was a lab assessment on my own virtual machine, not a test of the club's live network.

## 2. Server hardening (Task 1)

- Installed OpenSSH server and used an ED25519 SSH key to access the `falconadmin` account.
- Set `PermitRootLogin no`, `PasswordAuthentication no`, `KbdInteractiveAuthentication no` and `PubkeyAuthentication yes`.
- Confirmed the effective SSH settings using `sudo sshd -T`. Root and password-based SSH login attempts were rejected.
- Created a non-root account, `falconadmin`, with limited sudo access to check UFW status.
- Enabled UFW with **deny incoming** and **allow outgoing** defaults. The only incoming allow rules were TCP **22** (SSH) and **80** (HTTP), with corresponding IPv6 rules.
- Confirmed SSH key login still worked after the firewall was enabled.

Configuration summaries are in `configs/`. The original Task 1 commands and test outputs are in `reports/task1-hardening.md` and `logs/ubuntu-terminal-task1.txt`. The combined Task 1 terminal screenshots are in `reports/task1-terminal-evidence.pdf`.

## 3. Reconnaissance results (Task 2)

Nmap scan of `127.0.0.1` on **16 November 2026**:

```text
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.18
80/tcp open  http    nginx 1.18.0 (Ubuntu)
Not shown: 65533 closed ports
```

At first, port **631** (CUPS printing) was open and port **80** was not. I disabled the CUPS service and started Nginx for the HTTP service. The next localhost scan found only **22** and **80** open. The complete result is in `reports/localhost_scan.txt`.

A localhost scan verifies services listening on the machine. It **does not** by itself prove what is reachable from other devices or through the firewall.

## 4. SSH log analysis (Task 2)

I temporarily enabled SSH password authentication in the isolated lab to generate failed login records, then restored `PasswordAuthentication no` and verified it with `sudo sshd -T`.

Three failed SSH password attempts against `falconadmin` were recorded on **16 November 2026**:

| Time (PKT) | User | Source IP | Result |
|---|---|---|---|
| 19:54:18 | falconadmin | 10.0.2.2 | Failed password |
| 19:54:43 | falconadmin | 10.0.2.2 | Failed password |
| 19:54:51 | falconadmin | 10.0.2.2 | Failed password |

I wrote `scripts/analyze_logs.py` to read `logs/sample_auth.log` and print lines containing `Failed password`. It returned all three entries. The output is saved in `logs/log_analysis_output.txt`.

This is basic log filtering; it is not continuous intrusion detection or proof of an actual attack.

## 5. Remaining risks and recommendations

| Risk / limitation | Recommended next step |
|---|---|
| Many Ubuntu updates were pending during Task 1 | Install security updates and rescan the machine afterward |
| HTTP service on port 80 has no verified TLS setup | Configure HTTPS/TLS before using the registration app with real member data |
| Failed-login script is run manually | Schedule log monitoring and set alerts for repeated failures |
| Initial user password showed weak-password warnings | Confirm the `falconadmin` password was replaced with a strong, unique one |
| Only localhost was scanned | Run an authorized scan from another lab VM to confirm network-side exposure and UFW behavior |
| No verified web-app security assessment or backups | Add application testing, backups and access review before production use |

## 6. Handover and next steps

The required lab hardening, localhost scan and three-line SSH log check were demonstrated. The next priority is patching Ubuntu, protecting the registration app with HTTPS, and setting up regular monitoring and backups. Any future scan should stay within an approved testing scope.

**Files:** `README.md` explains how to reproduce the work; `configs/`, `scripts/`, `logs/`, `reports/` and `evidence/` contain the supporting material.

**Evidence limitation:** The SSH settings in `configs/` are recorded verified values, not an export of the full SSH configuration. A VirtualBox snapshot and a later strong-password change were not confirmed in the supplied materials.
