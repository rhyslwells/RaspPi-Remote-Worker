# ## B. The "Pulse" (Connectivity)

# A script using `smtplib` to send a summary of the Pi's system health (CPU temp, disk space) every hour.

# **Why:** Leverages the Pi's "always-on" nature.

# **Action:**
# - Collects system metrics (CPU temperature, disk space, memory usage)
# - Updates a trend-line chart directly in the Google Sheet
# - Stores the output in the Google Sheet Log

# **Implementation:**
# - Use `psutil` to gather system stats
# - Format data for Google Sheets integration
# - Append to a "System Health" tab with timestamps


Each script should:
- Accept parameters from the Google Sheet
- Log execution details (duration, status, errors)
- Update the Sheet with results
- Handle errors gracefully