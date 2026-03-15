# Troubleshooting SD Card Formatting Issues in Windows

When preparing your microSD card for Raspberry Pi, you may encounter the error:

```
When Windows reports **“Windows was unable to complete the format”**, the issue is usually one of the following:

* Corrupted partition table
* Read-only state on the card
* Multiple incompatible partitions (common after Linux/Raspberry Pi use)
* A failing or counterfeit SD card

The most reliable fix is to **wipe the partition table completely using DiskPart**.

#storage #filesystem #sdcard #windows

---

## 1. Reset the Card Using DiskPart

Open **Command Prompt as Administrator**.

Run the following commands step by step.

```
diskpart
list disk
```

You will see a list such as:

```
Disk 0   500 GB
Disk 1   64 GB
```

Identify the **microSD card by size**.

Then run:

```
select disk X
```

Where $X$ is the number of the SD card.

Next:

```
clean
```

This removes the entire partition table.

Now recreate it:

```
create partition primary
format fs=exfat quick
assign
exit
```

After this, Windows should detect roughly

$$
64,GB \rightarrow \approx 59,GB \text{ usable}
$$

---

## 2. If `clean` Fails

Sometimes the card becomes **read-only**.

Run this before `clean`:

```
attributes disk clear readonly
```

Full sequence:

```
select disk X
attributes disk clear readonly
clean
create partition primary
format fs=exfat quick
assign
```

---

## 3. If DiskPart Still Fails

Two likely causes remain:

### A. Corrupted firmware on the card

Use the **SD Card Formatter** from the SD Association (more reliable than Windows formatting).

### B. Counterfeit or damaged card

A common symptom is reporting **64 GB but only allowing ~512 MB**.

Verification tool:

* **H2testw**

---

## Quick Check

When you ran `list disk`, **did the SD card show as 64 GB or ~600 MB?**

That detail determines whether this is a **partition issue** or a **fake/failing card**.
