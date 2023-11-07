## Introduction
`main.py` - This script can check for the latest open issues, find if they're applied or not, and apply to all opened issues or the last one only. These options are configurable using shell flags accepted by the script. The script only look for **Ordinary IPO shares**.

## Instructions

- Install `python3`
- Create an `accounts.csv` file with the same format as [accounts.csv.example](accounts.csv.example) 
- `python3 main.py --help` for help

### Usage:
```
usage: main.py [-h] [-o] [-a] [-n N]

MeroShare simplified for bulk actions.
    - Find latest open issues
    - Check the applied/unapplied issues
    - Check IPO results

options:
  -h, --help  show this help message and exit
  -o          check if currently open issues are applied or unapplied
  -a          apply to all unapplied, default False (means apply to the latest opened issue only)
  -n N        number of shares to apply, default is 10
```

### Screenshots
<img width="902" alt="Screenshot 2023-11-07 at 10 29 59" src="https://github.com/ayerdines/meroshare-scripts/assets/34019794/ce60ef47-a4da-4024-9ffa-b244f0f62464">

### WIP
- Feature to check the results of IPO allotments
