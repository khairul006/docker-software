# Windows Server SSH Setup Guide

Notes for enabling OpenSSH Server on Windows Server and configuring key-based authentication.

---

## 1. Check if OpenSSH Server is installed

```powershell
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'
```

`State` will show `Installed` or `NotPresent`.

If not installed:

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
```

---

## 2. Check and start the sshd service

```powershell
Get-Service sshd | Select-Object Name, Status, StartType
```

If `Status` is `Stopped` and/or `StartType` is `Manual`, fix it:

```powershell
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
```

Re-check to confirm `Status: Running` and `StartType: Automatic`.

### Optional: enable ssh-agent too (needed for key-based auth workflows)

```powershell
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent
```

---

## 3. Check the firewall rule (port 22)

```powershell
Get-NetFirewallRule -Name *ssh*
```

Should show `OpenSSH-Server-In-TCP` enabled, allowing inbound TCP 22.

If missing:

```powershell
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

If this is a cloud VM (Azure/AWS/etc.), also confirm port 22 is open at the network/NSG/security-group level, not just the local Windows firewall.

---

## 4. Generate a key pair (on the client machine)

```powershell
ssh-keygen -t ed25519 -C "your-email-or-label"
```

- Accept the default path (`~/.ssh/id_ed25519`) unless you need a custom one.
- Optionally set a passphrase.
- This creates two files: `id_ed25519` (private — never share) and `id_ed25519.pub` (public — goes on the server).

The public key file contains **one line**, e.g.:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGVYourActualKeyDataHere... your-email-or-label
```

Copy the **entire line** exactly as-is (key type + base64 data + comment) when placing it on the server. No line breaks in the middle, no trimming.

---

## 5. Place the public key on the server

Where it goes depends on the connecting Windows account.

### Case A — Administrator account

Windows OpenSSH uses a special shared file for admin users (NOT the normal per-user `authorized_keys`):

```
C:\ProgramData\ssh\administrators_authorized_keys
```

Create/edit it (create fresh via PowerShell to avoid Notepad silently adding `.txt`):

```powershell
New-Item -Path "C:\ProgramData\ssh\administrators_authorized_keys" -ItemType File -Force
notepad "C:\ProgramData\ssh\administrators_authorized_keys"
```

Paste in the public key line(s), one per line, save with **Ctrl+S** (file already exists, so Notepad won't prompt for a name/extension).

Then lock down permissions — this file **must** be restricted to Administrators + SYSTEM only, or sshd rejects it:

```powershell
icacls.exe "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r
icacls.exe "C:\ProgramData\ssh\administrators_authorized_keys" /grant "Administrators:F"
icacls.exe "C:\ProgramData\ssh\administrators_authorized_keys" /grant "SYSTEM:F"
```

### Case B — Standard (non-admin) user

Use the normal per-user location:

```
C:\Users\<username>\.ssh\authorized_keys
```

Create the `.ssh` folder and file if needed, paste in the public key, then restrict permissions to that user + SYSTEM + Administrators:

```powershell
icacls.exe "C:\Users\<username>\.ssh\authorized_keys" /inheritance:r
icacls.exe "C:\Users\<username>\.ssh\authorized_keys" /grant "<username>:F"
icacls.exe "C:\Users\<username>\.ssh\authorized_keys" /grant "SYSTEM:F"
icacls.exe "C:\Users\<username>\.ssh\authorized_keys" /grant "Administrators:F"
```

---

## 6. Check permissions before/after changes

**View current ACLs (read-only):**

```powershell
icacls.exe "C:\ProgramData\ssh\administrators_authorized_keys"
```

or

```powershell
Get-Acl "C:\ProgramData\ssh\administrators_authorized_keys" | Format-List
```

**What's wrong:** any entry besides `Administrators` and `SYSTEM` (e.g. `Users`, `Everyone`, `Authenticated Users`) — sshd will refuse to use the file if extra accounts have access.

**What "correct" looks like:**

- `administrators_authorized_keys`:
  ```
  BUILTIN\Administrators:(F)
  NT AUTHORITY\SYSTEM:(F)
  ```
- per-user `authorized_keys`:
  ```
  <username>:(F)
  NT AUTHORITY\SYSTEM:(F)
  BUILTIN\Administrators:(F)
  ```

`/inheritance:r` strips inherited permissions (clears out stray `Users`/`Everyone` entries) before you explicitly `/grant` the correct ones.

---

## 7. Troubleshooting: "the system cannot find the file specified"

If `icacls.exe` can't find a file you just created:

- **Check for a hidden `.txt` extension** (common when Notepad's Save-As added it):
  ```powershell
  dir C:\ProgramData\ssh\
  ```
  If you see `administrators_authorized_keys.txt`, rename it:
  ```powershell
  Rename-Item "C:\ProgramData\ssh\administrators_authorized_keys.txt" "administrators_authorized_keys"
  ```
- **Confirm the ssh folder path is correct:**
  ```powershell
  Test-Path "C:\ProgramData\ssh"
  ```
- **Confirm sshd's actual binary path** (in case of a non-default install):
  ```powershell
  Get-Service sshd | Select-Object -ExpandProperty BinaryPathName
  ```
- Safest fix: create the file via PowerShell (`New-Item`) rather than Notepad's Save-As, which avoids extension confusion entirely.

---

## 8. Confirm sshd_config allows key auth

Check `C:\ProgramData\ssh\sshd_config` for:

```
PubkeyAuthentication yes
```

Usually enabled by default. Restart the service after any config change:

```powershell
Restart-Service sshd
```

---

## 9. Test the connection

From the client:

```powershell
ssh -i ~/.ssh/id_ed25519 username@server-ip
```

If it still prompts for a password, use verbose mode to see why key auth was skipped/rejected:

```powershell
ssh -v -i ~/.ssh/id_ed25519 username@server-ip
```

---

## 10. (Optional) Disable password auth

Only after confirming key-based login works, to avoid locking yourself out.

In `sshd_config`:

```
PasswordAuthentication no
```

Then:

```powershell
Restart-Service sshd
```