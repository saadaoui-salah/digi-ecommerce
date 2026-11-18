#!/usr/bin/env python3
"""SSH/SCP tripwire.

Watches the SSH authentication log. When it sees

  * an authentication with a PASSWORD, or
  * a public-key authentication whose fingerprint is not on the allowlist,

it wipes the deployed code and the Docker images, but leaves the database
alone. SCP/SFTP is covered: it authenticates over the same SSH connection, so
the offending auth line is the one that triggers the wipe.

This is a last-resort tripwire, not a substitute for turning password
authentication off in sshd_config. Read ops/ssh-tripwire/README.md before
installing it.

DRY RUN IS THE DEFAULT. Nothing is deleted until "dry_run" is false in the
config file and the kill-switch file is absent.
"""

from __future__ import annotations

import argparse
import configparser
import ipaddress
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_CONFIG = Path("/etc/ssh-tripwire.conf")
DEFAULT_KILL_SWITCH = Path("/etc/ssh-tripwire.disabled")

# Lines the OpenSSH daemon writes for a successful login.
PASSWORD_RE = re.compile(
    r"Accepted password for (?P<user>\S+) from (?P<ip>\S+) port \d+"
)
PUBLICKEY_RE = re.compile(
    r"Accepted publickey for (?P<user>\S+) from (?P<ip>\S+) port \d+"
    r"(?: ssh2:)?\s*(?P<algo>\S+)\s+(?P<fingerprint>SHA256:\S+|[0-9a-f:]+)"
)
SUBSYSTEM_RE = re.compile(
    r"subsystem request for (?P<subsystem>\S+) by user (?P<user>\S+) from (?P<ip>\S+)"
)

# Paths the tripwire must never delete, whatever the config says.
FORBIDDEN_PATHS = {
    Path("/"),
    Path("/etc"),
    Path("/var"),
    Path("/usr"),
    Path("/home"),
    Path("/root"),
    Path("/proc"),
    Path("/sys"),
    Path("/dev"),
    Path("/boot"),
}

log = logging.getLogger("ssh-tripwire")


class ConfigError(RuntimeError):
    """The config is missing, unsafe or incomplete."""


class Event:
    """A successful authentication the tripwire cares about."""

    def __init__(self, kind: str, user: str, ip: str, line: str, fingerprint: str = ""):
        self.kind = kind
        self.user = user
        self.ip = ip
        self.line = line.strip()
        self.fingerprint = fingerprint

    def __str__(self) -> str:
        extra = f" fingerprint={self.fingerprint}" if self.fingerprint else ""
        return f"{self.kind} user={self.user} ip={self.ip}{extra}"


def load_config(path: Path) -> dict:
    """Read and validate the config file."""
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")

    parser = configparser.ConfigParser()
    parser.read(path)

    def get_list(section: str, option: str) -> list[str]:
        raw = parser.get(section, option, fallback="")
        return [item.strip() for item in raw.replace("\n", ",").split(",") if item.strip()]

    config = {
        "log_file": Path(parser.get("main", "log_file", fallback="/var/log/ssh-tripwire.log")),
        "auth_log": Path(parser.get("main", "auth_log", fallback="/var/log/auth.log")),
        "dry_run": parser.getboolean("main", "dry_run", fallback=True),
        "allowed_ips": get_list("allowlist", "allowed_ips"),
        "allowed_fingerprints": get_list("allowlist", "allowed_fingerprints"),
        "code_paths": [Path(p) for p in get_list("targets", "code_paths")],
        "compose_projects": get_list("targets", "compose_projects"),
        "protected_paths": [Path(p) for p in get_list("targets", "protected_paths")],
        "docker_images": parser.getboolean("targets", "docker_images", fallback=True),
    }

    if not config["code_paths"] and not config["compose_projects"]:
        raise ConfigError("no code_paths or compose_projects configured — refusing to do nothing")

    if not config["protected_paths"]:
        raise ConfigError("no protected_paths configured — the database would not be safe")

    for path in config["code_paths"] + config["protected_paths"]:
        resolved = path.resolve()
        if resolved in FORBIDDEN_PATHS or len(resolved.parts) < 3:
            raise ConfigError(f"refusing a dangerously broad path: {path}")

    for fingerprint in config["allowed_fingerprints"]:
        if not (fingerprint.startswith("SHA256:") or ":" in fingerprint):
            raise ConfigError(f"not an SSH key fingerprint: {fingerprint}")

    for ip in config["allowed_ips"]:
        try:
            ipaddress.ip_network(ip, strict=False)
        except ValueError as exc:
            raise ConfigError(f"not an IP or CIDR: {ip}") from exc

    return config


def parse_line(line: str, config: dict) -> Event | None:
    """Turn an auth.log line into an event, or ignore it."""
    password = PASSWORD_RE.search(line)
    if password:
        return Event("password", password["user"], password["ip"], line)

    publickey = PUBLICKEY_RE.search(line)
    if publickey:
        fingerprint = publickey["fingerprint"]
        if is_allowed_ip(publickey["ip"], config["allowed_ips"]) and fingerprint in config["allowed_fingerprints"]:
            return None
        return Event(
            "publickey",
            publickey["user"],
            publickey["ip"],
            line,
            fingerprint,
        )

    # An SCP/SFTP transfer is useful context in the log, but the auth line
    # above is the one that decides. It is reported when it comes from an IP
    # that is not allowed, so a transfer after a valid login is not ignored.
    subsystem = SUBSYSTEM_RE.search(line)
    if subsystem and not is_allowed_ip(subsystem["ip"], config["allowed_ips"]):
        return Event("scp", subsystem["user"], subsystem["ip"], line)

    return None


def is_allowed_ip(address: str, allowed: list[str]) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False

    return any(ip in ipaddress.ip_network(item, strict=False) for item in allowed)


def wipe(event: Event, config: dict, kill_switch: Path) -> None:
    """Delete the code and the Docker images, keeping the database."""
    log.critical("TRIGGERED: %s", event)

    if kill_switch.exists():
        log.warning("kill switch %s exists — no action taken", kill_switch)
        return

    if config["dry_run"]:
        log.warning("dry run — no action taken (set dry_run=false in the config to arm)")
        return

    # The database must be safe before and after the wipe.
    for path in config["protected_paths"]:
        if not path.exists():
            raise ConfigError(f"protected path does not exist: {path}")

    for project in config["compose_projects"]:
        # No --volumes: the database lives in a Docker volume.
        command = ["docker", "compose", "-p", project, "down", "--rmi", "all"]
        run(command)

    for path in config["code_paths"]:
        if not path.exists():
            log.info("code path already gone: %s", path)
            continue
        log.warning("removing code path %s", path)
        shutil.rmtree(path)

    if config["docker_images"]:
        run(["docker", "image", "prune", "-a", "-f"])

    for path in config["protected_paths"]:
        if not path.exists():
            log.critical("PROTECTED PATH LOST: %s", path)

    log.critical("wipe finished; database paths were left in place")


def run(command: list[str]) -> None:
    """Run a command and log what it did."""
    log.info("running: %s", " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.stdout.strip():
        log.info(result.stdout.strip())
    if result.returncode:
        log.error("command failed (%s): %s", result.returncode, result.stderr.strip())


def follow(config: dict, kill_switch: Path) -> None:
    """Tail the auth log and react to new lines."""
    auth_log = config["auth_log"]
    if not auth_log.exists():
        raise ConfigError(f"auth log not found: {auth_log}")

    log.info("watching %s (dry_run=%s)", auth_log, config["dry_run"])

    with auth_log.open("r", encoding="utf-8", errors="replace") as stream:
        stream.seek(0, os.SEEK_END)
        while True:
            line = stream.readline()
            if not line:
                time.sleep(0.5)
                continue

            event = parse_line(line, config)
            if event:
                log.info("auth event: %s", event)
                wipe(event, config, kill_switch)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--kill-switch", type=Path, default=DEFAULT_KILL_SWITCH)
    parser.add_argument("--check", action="store_true", help="validate the config and exit")
    parser.add_argument("--test-line", help="feed one log line through the rules (no wipe)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("/var/log/ssh-tripwire.log", encoding="utf-8"),
        ],
    )

    try:
        config = load_config(args.config)
    except (ConfigError, configparser.Error) as exc:
        log.critical("config error: %s", exc)
        return 2

    if args.check:
        log.info("config OK (dry_run=%s)", config["dry_run"])
        return 0

    if args.test_line:
        event = parse_line(args.test_line, config)
        log.info("matched: %s", event or "nothing")
        return 0

    def stop(_signum, _frame):
        log.info("stopping")
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    follow(config, args.kill_switch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
