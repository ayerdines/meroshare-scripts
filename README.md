## Instructions

- Install python3
- Create a `accounts.csv` file with same format as [accounts.csv.example](accounts.csv.example) 
- `python3 main.py --help` to know the options

### Usage:

```shell
usage: main.py [-h] [-o] [-a] [-n N]

MeroShare simplified for bulk actions.
    - Find open issues
    - Check applied issue
    - Check IPO allotments

options:
  -h, --help  show this help message and exit
  -o          check if currently open issues are applied or unapplied
  -a          apply to all unapplied, default False (means apply to the latest opened issue only)
  -n N        number of shares to apply, default is 10
```