# Implementation Ideas

Since you are interested in computational operations and data, here are three directions for your `/scripts` folder:

## A. The Prime Hunter (Computational)

A script that finds the next `n` prime numbers starting from a stored value.

**Why:** Demonstrates long-running CPU tasks.

**Action:** The Pi calculates, then appends the results to a "Log" tab in your Google Sheet.

**Implementation:**
- Store the current search position in a database or config file
- Use an efficient prime-finding algorithm
- Log results with timestamps
- Update Google Sheet with findings

---

## B. The "Pulse" (Connectivity)

A script using `smtplib` to send a summary of the Pi's system health (CPU temp, disk space) every hour.

**Why:** Leverages the Pi's "always-on" nature.

**Action:**
- Collects system metrics (CPU temperature, disk space, memory usage)
- Updates a trend-line chart directly in the Google Sheet
- Stores the output in the Google Sheet Log

**Implementation:**
- Use `psutil` to gather system stats
- Format data for Google Sheets integration
- Append to a "System Health" tab with timestamps

---

## Getting Started

1. Start with **The Prime Hunter** - it's pure computation with no external dependencies
2. Implement **The Pulse** next - adds system monitoring

Each script should:
- Accept parameters from the Google Sheet
- Log execution details (duration, status, errors)
- Update the Sheet with results
- Handle errors gracefully
