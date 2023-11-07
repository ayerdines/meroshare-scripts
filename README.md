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
![Screenshot 2023-11-07 at 20.44.08.png](..%2F..%2F..%2F..%2Fvar%2Ffolders%2Ffd%2Fj830xrzn51g4qr1xl5__ysrh0000gn%2FT%2FTemporaryItems%2FNSIRD_screencaptureui_7swK11%2FScreenshot%202023-11-07%20at%2020.44.08.png)

### WIP
- Feature to check the results of IPO allotments
