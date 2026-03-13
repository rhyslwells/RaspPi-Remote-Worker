# ## A. The Prime Hunter (Computational)

# A script that finds the next `n` prime numbers starting from a stored value.

# **Why:** Demonstrates long-running CPU tasks.

# **Action:** The Pi calculates, then appends the results to a "Log" tab in your Google Sheet.

# **Implementation:**
# - Store the current search position in a database or config file
# - Use an efficient prime-finding algorithm
# - Log results with timestamps
# - Update Google Sheet with findings

Each script should:
- Accept parameters from the Google Sheet
- Log execution details (duration, status, errors)
- Update the Sheet with results
- Handle errors gracefully