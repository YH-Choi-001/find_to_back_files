# Find all the files to be backed up

## Background

I make a full backup of my mac to my family's NAS every year.
The backup mostly consists of my `Desktop/`, `Documents/` and `Downloads/` folders.

Usually the `Desktop/` and `Downloads/` folders are < 1 GB, but my `Documents/` folder
could be as large as 30 GB.

My dad complains about this, and asks me to perform incremental backups instead.

To make my life easier, I need to find all the files that were modified after the previous backup timestamp.

Using the `find` command is simple but ineffective.
It reports all the modified files, but I want to get the parent folder if all its children are modified after the timestamp.
This makes my life easier when trying to identify which folders need to be backed up.

Hence I've created this python script to locate the files to be backed up.

One thing worth noting is that, I use Git and GitHub to store my source code,
and the development virtual environments are usually very large but need not to be backed up,
because we have dependencies defined in `requirements.txt` or `package.json`
together with lockfiles (`poetry.lock`, `package-lock.json`).
We can easily recreate the virtual environments after restoring the source code.
Thus, I rarely backup my source code nor the virtual environments.

## Usage

```bash
python3 find_to_back_files.py --since "2025-09-15 00:00:00" > files_edited_after_20250915.txt
```
