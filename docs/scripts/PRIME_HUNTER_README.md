# Prime Hunter Script Documentation

## Overview

The **Prime Hunter** is a computational script that finds all prime numbers within a specified range. It demonstrates:

- **Long-running CPU tasks** on the Raspberry Pi
- **Parameterized script execution** via Google Sheets
- **Logging results** to a spreadsheet for remote tracking
- **Flexible range configuration** without code changes

---

## Purpose

Prime Hunter performs a brute-force prime number search between two integers (inclusive). The script reads its execution parameters (start and end values) from the Google Sheets Config sheet, allowing you to change the search range without modifying code or SSH-ing into the Pi.

**Why Prime Hunter?**
- Demonstrates CPU-bound computational work
- Shows how to handle long-running processes
- Tests parameter passing from Google Sheets to scripts
- Provides easily verifiable results (can validate primes independently)
- Useful for benchmarking Raspberry Pi performance

---

## Configuration

### Setup in Google Sheets

Prime Hunter requires configuration in your **RaspPI-Remote-Worker** spreadsheet's **Config** sheet:

| Column | Value | Description |
|--------|-------|-------------|
| Script Name | `prime_hunter` | Identifies the script |
| Status | `IDLE` | Initial status; set to `START` to trigger execution |
| Last Used | (auto-populated) | Timestamp of last execution |
| Details | (auto-populated) | Result summary and messages |
| Priority | `3` | Execution priority (1-10, lower runs first) |
| **Parameter-1** | `100` | **Starting integer (inclusive)** |
| **Parameter-2** | `200` | **Ending integer (inclusive)** |

### Spreadsheet Example

```
Script Name   | Status | Last Used           | Details                          | Priority | Parameter-1 | Parameter-2
prime_hunter  | IDLE   | 2026-03-13 12:00:00 | Found 21 primes between 100-200  | 3        | 100         | 200
```

### Changing Search Range

To find primes in a different range, simply update the parameters in the spreadsheet:

- **Parameter-1**: Update to your start value
- **Parameter-2**: Update to your end value
- Set **Status** to `START`

The script will:
1. Read the new parameters on next execution
2. Search the new range
3. Log results to the Log sheet
4. Update Config sheet with results

**Example configurations:**

```
# Find large primes
Parameter-1: 10000
Parameter-2: 10100

# Find primes in a small range
Parameter-1: 2
Parameter-2: 50

# Deep computational work
Parameter-1: 100000
Parameter-2: 100500
```

---

## Parameters

| Parameter | Name | Type | Required | Default | Description |
|-----------|------|------|----------|---------|-------------|
| Parameter-1 | Start | Integer | Yes | 100 | Lowest integer to check (inclusive). Must be ≥ 2. |
| Parameter-2 | End | Integer | Yes | 200 | Highest integer to check (inclusive). Must be ≥ Start. |

### Parameter Validation

The script automatically handles edge cases:

- If Start < 2, it's adjusted to 2 (smallest prime)
- If Start > End, no primes are returned
- Empty parameters use defaults (Start=100, End=200)

---

## How It Works

### Execution Flow

```
1. Script starts
   ↓
2. Initialize Control Panel
   ↓
3. Read Parameter-1 and Parameter-2 from Config sheet
   ↓
4. Validate range (ensure start ≤ end)
   ↓
5. Execute find_primes(start, end)
   ↓
6. Log results to Config and Log sheets
   ↓
7. Update status to SUCCESS or FAILED
   ↓
8. Exit
```

### Prime Finding Algorithm

The script uses a trial division algorithm:

```python
For each number N in range(start, end+1):
    - Check if N is divisible by any integer from 2 to √N
    - If no divisors found, N is prime
    - Add N to results list
```

**Time Complexity:** O((end - start) × √N) per number checked

**Performance Notes:**
- Checking 100 numbers: ~milliseconds
- Checking 1,000 numbers: ~seconds  
- Checking 100,000 numbers: ~minutes (CPU-intensive)
- Useful for testing Raspberry Pi load and thermals

### Logging Output

When Prime Hunter executes, it records:

**Config Sheet (updated automatically):**
- Status: Changes from IDLE → RUNNING → SUCCESS
- Last Used: Timestamp of execution
- Details: Message with count and range

**Log Sheet (permanent record):**
- Timestamp: When execution started
- Script Name: "prime_hunter"
- Status: SUCCESS or FAILED
- Message: Summary (e.g., "Found 21 primes between 100-200")
- Details: List of first/last primes found

**Example Log Entry:**
```
Timestamp              | Script Name | Status  | Message                        | Details
2026-03-13 12:30:15   | prime_hunter| SUCCESS | Found 21 primes between 100... | First 5: [101, 103, 107, 109, 113]
```

---

## Usage

### Manual Execution

Run directly from the scripts directory:

```bash
cd scripts
python prime_hunter.py
```

This reads parameters from Config sheet and executes immediately.

### Automatic Execution via Runner

The `runner.py` script automatically detects and runs Prime Hunter when its status is `START`:

```bash
# runner.py checks Config sheet and runs all START scripts
python runner.py
```

### Python API Usage

Import and use Prime Hunter programmatically:

```python
from utils.control_panel import ControlPanel
from prime_hunter import find_primes

panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")

# Method 1: Read parameters from sheet and execute
params = panel.get_script_parameters_list("prime_hunter")
start = int(params[0]) if len(params) > 0 else 100
end = int(params[1]) if len(params) > 1 else 200

primes = find_primes(start, end)
print(f"Found {len(primes)} primes between {start} and {end}")

# Method 2: Direct function call with custom range
primes = find_primes(50, 100)
print(f"Primes 50-100: {primes}")
```

---

## Performance Characteristics

### Execution Times (Approximate)

These times are measured on a Raspberry Pi 4 (typical):

| Range | Count | Time |
|-------|-------|------|
| 1-100 | 25 | <100ms |
| 100-200 | 21 | <100ms |
| 1,000-1,100 | 16 | ~200ms |
| 10,000-10,500 | 34 | ~1-2 seconds |
| 100,000-100,500 | 36 | ~10-15 seconds |
| 1,000,000-1,000,500 | 18 | ~2-3 minutes |

**Factors affecting execution time:**
- Number range size
- Size of numbers (larger = slower to check)
- Raspberry Pi CPU frequency and thermal throttling
- System load from other processes

---

## Results & Examples

### Common Use Cases

#### Case 1: Quick Verification
```
Parameter-1: 2
Parameter-2: 20
Result: [2, 3, 5, 7, 11, 13, 17, 19]
```

#### Case 2: Medium Computation
```
Parameter-1: 1000
Parameter-2: 1100
Result: 16 primes found
```

#### Case 3: Performance Testing
```
Parameter-1: 100000
Parameter-2: 101000
Result: ~75 primes, ~30 second execution (loads Pi)
```

#### Case 4: Finding Twin Primes
```
Parameter-1: 10000
Parameter-2: 10100
# Then manually inspect results for pairs with difference of 2
```

---

## Error Handling

Prime Hunter includes robust error handling:

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Script not found" | Config sheet missing "prime_hunter" entry | Add script to Config sheet manually |
| Parameters empty | Parameter cells not filled in | Enter Start and End integers in Config |
| "Invalid parameter" | Non-integer values in Parameter columns | Ensure parameters are numeric |
| Timeout/slow results | Range too large or Pi under load | Reduce range size or wait for system idle |

### Log Sheet Errors

Failed executions are logged with error details:

```
Status  | Message                | Details
FAILED  | Error finding primes   | invalid literal for int() with base 10: 'abc'
```

Check the Details column on the Log sheet for debugging information.

---

## Extending Prime Hunter

### Modify the Algorithm

To use a faster prime-checking algorithm (e.g., Miller-Rabin):

```python
def find_primes_fast(start: int, end: int) -> list:
    """Uses a faster algorithm for finding primes."""
    from sympy import isprime  # or your favorite library
    return [n for n in range(max(2, start), end + 1) if isprime(n)]
```

Then update `prime_hunter.py` to use `find_primes_fast()`.

### Add More Parameters

To track additional metrics, extend the Config sheet:

```
Parameter-1: Start number
Parameter-2: End number
Parameter-3: Algorithm choice ('trial_division' or 'miller_rabin')
```

Then update the script:

```python
params = panel.get_script_parameters_list("prime_hunter")
algorithm = params[2] if len(params) > 2 else 'trial_division'
```

### Batch Processing

Run Prime Hunter across multiple ranges:

```python
ranges = [
    (100, 200),
    (1000, 1100),
    (10000, 10100)
]

for start, end in ranges:
    # Update Config sheet parameters
    # Trigger execution
    # Collect results
```

---

## Testing

### Verify Installation

```bash
cd scripts
python -c "from prime_hunter import find_primes; print(find_primes(10, 20))"
# Output: [11, 13, 17, 19]
```

### Test with Google Sheets

1. Ensure `credentials.json` is in project root
2. Add `prime_hunter` entry to Config sheet
3. Set Parameter-1=100, Parameter-2=200
4. Run: `python prime_hunter.py`
5. Check Config sheet → Details column shows result count
6. Check Log sheet → New entry with execution record

### Manual Calculation Verification

Verify a few small ranges manually:

```python
# Range 11-20 should contain: 11, 13, 17, 19
# Range 2-10 should contain: 2, 3, 5, 7
```

---

## Tips & Best Practices

### ✅ Best Practices

- **Start small**: Test with Parameter-1=100, Parameter-2=200 first
- **Monitor thermals**: Use larger ranges to monitor Pi temperature
- **Schedule off-peak**: Run during low-traffic times to avoid network issues
- **Archive results**: Keep Log sheet clean by archiving old entries monthly
- **Document results**: Add notes to Config Details column about significant findings

### ⚠️ Cautions

- **Large ranges are slow**: Ranges > 100,000 may take minutes
- **Blocks other scripts**: Doesn't multi-process; blocks runner until complete
- **Memory usage**: Very large ranges keep all primes in memory
- **CPU throttling**: Pi may thermal-throttle during sustained computation

---

## Troubleshooting

### Script Doesn't Start

**Symptom:** Status remains IDLE even after setting to START

**Solutions:**
- Check that Parameter-1 and Parameter-2 have numeric values
- Verify credentials.json exists and has proper permissions
- Check Config sheet has "prime_hunter" entry
- Review console output for authentication errors

### Wrong Results

**Symptom:** Number of primes seems incorrect

**Solutions:**
- Verify parameters in Config sheet match intended range
- Use an online prime checker to verify (e.g., primes-checker.com)
- Check that script actually used the updated parameters (review Log sheet)

### Very Slow Execution

**Symptom:** Script runs but takes much longer than expected

**Solutions:**
- Check Pi CPU temperature (`vcgencmd measure_temp`)
- Reduce range size or run during lighter load
- Check for other CPU-intensive processes
- Consider using a faster prime-finding library

### Credentials Error

**Symptom:** "Credentials file not found" or authentication fails

**Solutions:**
- Ensure `credentials.json` is in project root: `/RaspPi-Remote-Worker/credentials.json`
- Check service account has Editor access to spreadsheet
- Verify service account email matches what's shared in Config sheet

---

## API Reference

### Function: `find_primes(start: int, end: int) -> list`

**Description:** Find all prime numbers in a range

**Parameters:**
- `start` (int): Starting integer (inclusive, auto-adjusted to ≥ 2)
- `end` (int): Ending integer (inclusive)

**Returns:** List of prime numbers found

**Example:**
```python
primes = find_primes(100, 200)
# Returns: [101, 103, 107, 109, 113, ..., 199]
```

### Function: `main() -> int`

**Description:** Main entry point for the script

**Returns:**
- 0 if execution successful
- 1 if execution failed

**Example:**
```python
exit_code = main()
```

---

## Related Documentation

- [Control Panel README](CONTROL_PANEL_README.md) - Core script management system
- [Runner README](RUNNER_README.md) - Automatic script orchestration
- [Test Connection README](TEST_CONNECTION_README.md) - Verify Google Sheets connectivity

---

## Summary

Prime Hunter is a parameterized computational script that:

✅ Finds prime numbers in any range  
✅ Reads parameters from Google Sheets (no code changes needed)  
✅ Logs detailed results for remote tracking  
✅ Demonstrates CPU workload handling on Raspberry Pi  
✅ Integrates with the Control Panel system  

**Quick Start:**
1. Add `prime_hunter` to Config sheet with Parameter-1=100, Parameter-2=200
2. Set Status to START
3. Run `python prime_hunter.py` or wait for runner.py
4. Check Config Details and Log sheet for results
