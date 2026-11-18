# SSH / SCP tripwire

A last-resort script for **2.25.13.160** (the separate server, not the Hostinger VPS in this account). It watches the SSH authentication log and, when it sees a login that should not have happened, deletes the deployed code and the Docker images while leaving the database in place.

> **WARNING — THIS IS DESTRUCTIVE.** A false positive wipes the app. It is **not** a replacement for disabling password authentication in `sshd_config`; do that first. Nothing is deleted until `dry_run=false` and the kill-switch file is removed.

## What triggers it

| Event in `auth.log` | Action |
| --- | --- |
| `Accepted password for …` | Wipe — **any** password login, from any IP |
| `Accepted publickey for …` with a fingerprint that is **not** in `allowed_fingerprints` from an IP that is **not** in `allowed_ips` | Wipe |
| An SCP/SFTP subsystem request from an IP that is not allowed | Logged as a trigger (the auth line above is what decides) |

A key login from one of your IPs **with** your fingerprint is ignored. An SCP or SFTP transfer that authenticates with your key from your IP is ignored too.

## What it deletes — and what it keeps

- Removes every path in `code_paths` (`shutil.rmtree`).
- Brings down each Compose project in `compose_projects` with `docker compose -p … down --rmi all` — **no `--volumes`**, so named volumes survive.
- Prunes all Docker images when `docker_images=true`.
- **Never** touches `protected_paths`. It checks that they exist before the wipe and logs a critical error if one disappears. Put your database file or the database's Docker volume directory here.

## Install (on 2.25.13.160, as root)

```bash
# 1. Install the files
mkdir -p /opt/ssh-tripwire
cp tripwire.py /opt/ssh-tripwire/
cp ssh-tripwire.service /etc/systemd/system/
cp tripwire.conf.example /etc/ssh-tripwire.conf
chmod 700 /opt/ssh-tripwire
chmod 600 /etc/ssh-tripwire.conf

# 2. Fill in the config: your IPs, your key fingerprint, the app paths and
#    the database paths that must survive.
ssh-keygen -lf ~/.ssh/id_ed25519.pub          # the SHA256 fingerprint
docker compose ps                             # the project name
nano /etc/ssh-tripwire.conf

# 3. Check the config and the rules without touching anything
python3 /opt/ssh-tripwire/tripwire.py --check
python3 /opt/ssh-tripwire/tripwire.py --test-line \
  'Accepted password for root from 203.0.113.5 port 54321 ssh2'

# 4. Start it in dry-run mode and watch the log
systemctl daemon-reload
systemctl enable --now ssh-tripwire
journalctl -u ssh-tripwire -f

# 5. ONLY WHEN YOU ARE SURE: arm it and remove the kill switch
sed -i 's/dry_run = true/dry_run = false/' /etc/ssh-tripwire.conf
touch /etc/ssh-tripwire.disabled   # emergency stop: recreating this file disables the action
systemctl restart ssh-tripwire
```

## Emergency stop

Create the kill-switch file — the watcher keeps running and logging but deletes nothing:

```bash
touch /etc/ssh-tripwire.disabled
```

## Hardening that matters more than this script

```bash
# /etc/ssh/sshd_config
PasswordAuthentication no
PermitRootLogin prohibit-password
AllowUsers youruser
```

Reload with `systemctl reload ssh`. With password authentication off, most of the trigger conditions can never happen — the tripwire then only catches a key that is not yours.

## Notes

- Needs Python 3 and root (to read `auth.log` and remove the app directory).
- On Ubuntu 24.04, `auth.log` is written by rsyslog; make sure `rsyslog` is running. If not, point `auth_log` at a file fed by `journalctl -u ssh -f`.
- The script re-reads the config only at startup, so restart the service after editing it.
- Test the rules with `--test-line` before arming; test the actual wipe on a scratch server, never on production.
