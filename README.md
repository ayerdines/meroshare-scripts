## Introduction
`main.py` - This script can check for the latest open issues, find if they're applied or not, and apply to all opened issues or the last one only. These options are configurable using shell flags accepted by the script. The script only look for **Ordinary IPO shares**.

## Instructions

- Install `python3`
- Create an `accounts.csv` file with the same format as [accounts.csv.example](accounts.csv.example) 
- `python3 main.py --help` for help

### Usage:
```
usage: main.py [-h] [-r] [-n NAME] [-a] [-id COMPANY_SHARE_ID] [-s SHARES]

MeroShare simplified for bulk actions.
    - Find currently open issues
    - Check issue status (applied, unapplied, allotted or not-allotted)

options:
  -h, --help            show this help message and exit
  -r, --report          Check IPO allotment reports
  -n NAME, --name NAME  Name of the user, runs the script for this user only, default is run for all users in accounts.csv file
  -a, --apply           Apply to issues
  -id COMPANY_SHARE_ID, --company-share-id COMPANY_SHARE_ID
                        Company share id to apply, required when -a/--apply flag is set
  -s SHARES, --shares SHARES
                        Number of shares to apply, default is 10
```

### Screenshots
<img width="875" alt="Screenshot 2023-11-07 at 20 45 57" src="https://github.com/ayerdines/meroshare-scripts/assets/34019794/6c2a0839-4abe-4781-a12e-27ce17e569e5">

### WIP
- Feature to check the results of IPO allotments
