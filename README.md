# Tor IP Rotator

A small, beginner-friendly GUI that automatically rotates your Tor exit IP
on a timer, by sending Tor's own `NEWNYM` signal through its ControlPort.

*Developed by MAHRAN*

## What this does

Tor already lets you request a new circuit (and so a new exit IP) at any
time — normally you'd do that by hand with a control-port command. This
app just automates that on a timer with a simple Start/Stop GUI, and shows
you your current exit IP so you can see it actually changing.

## Requirements

- Linux (tested on Kali / Debian-based distros)
- Tor installed and running, with its control port enabled
- Python 3

## 1. Install Tor and Python

```bash
sudo apt update
sudo apt install -y tor python3 python3-pip python3-tk
```

## 2. Enable Tor's control port

Edit `/etc/tor/torrc` and add:

```
ControlPort 9051
CookieAuthentication 1
```

Then restart Tor:

```bash
sudo systemctl enable --now tor
sudo systemctl restart tor
```

## 3. Install the Python dependencies

```bash
pip3 install -r requirements.txt --break-system-packages
```

## 4. Run it

```bash
python3 tor_ip_rotator.py
```

Set your interval (seconds) and hit **Start**. The log shows each
rotation, and the "Current exit IP" line updates automatically.

> **Note:** Tor rate-limits how often `NEWNYM` actually gets you a *new*
> circuit — intervals under ~10 seconds often won't change your exit IP
> every single time, and hammering it faster than that just loads the
> Tor network for no real benefit.

## A note on responsible use

This tool changes *which Tor exit node you appear to browse from* — it's
useful for privacy and for testing how your own services behave across
different source IPs. It is **not** a way to bypass a website's rate
limits, bans, or terms of service, and doing that is likely to violate
those terms regardless of the tool used. Use it on your own services or
for legitimate privacy/testing purposes.

## License

MIT — see [LICENSE](LICENSE).
