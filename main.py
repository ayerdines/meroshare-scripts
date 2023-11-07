import csv
import os
import argparse
import requests
import constants
from functools import cache, cached_property


def find_accounts_from_csv(name=None):
    acs = []
    with open(constants.ACCOUNTS_CSV_PATH, newline='') as file:
        csv_reader = csv.DictReader(file)
        if name:
            row = next((item for item in csv_reader if item['name'] == name), None)
            if row:
                return [Account(row['name'], row['dp'], row['username'], row['password'], row['crn'], row['pin'])]

            raise argparse.ArgumentError(name_arg, f"user with name: {name} not found in accounts.csv file")
        else:
            acs.extend([Account(row['name'], row['dp'], row['username'], row['password'], row['crn'], row['pin']) for row in csv_reader])

    return acs


class Account:
    def __init__(self, name, dp, username, password, crn, pin):
        self.name = name
        self.dp = dp
        self.client_id = self.get_client_id(dp)
        self.username = username
        self.password = password
        self.crn = crn
        self.pin = pin

    @staticmethod
    def get_client_id(dp):
        """
        :param dp: depository participant id
        :return: integer, client id in meroshare system
        """
        capital = next(item for item in constants.CAPITALS if item['code'] == str(dp))
        return capital['id']


class Issue:
    def __init__(self, json_data):
        self._json_data = json_data

    def __str__(self):
        return (
            "******   COMPANY SHARE ID: {company_share_id}    ******{sep}{share_type} ({share_group}) - {subgroup}"
            " ({symbol}) - {name}{sep}{open_date} - {close_date}{sep}{status}{sep}"
            .format(
                sep=os.linesep,
                company_share_id=self.company_share_id,
                name=self.company_name,
                subgroup=self.subgroup,
                symbol=self.scrip,
                open_date=self.issue_open_date,
                close_date=self.issue_close_date,
                share_type=self.share_type_name,
                share_group=self.share_group_name,
                status=self.status.capitalize())
            )

    @property
    def is_unapplied_ordinary_share(self):
        return self.is_ordinary_shares and not self.is_applied

    @property
    def is_ipo(self):
        return True if self.share_type_name == 'IPO' else False

    @property
    def is_fpo(self):
        return True if self.share_type_name == 'FPO' else False

    @property
    def is_ordinary_shares(self):
        return True if self.share_group_name == 'Ordinary Shares' else False

    @property
    def status(self):
        return "applied" if self.is_applied else "not applied"

    @property
    def is_applied(self):
        return True if self.action == "edit" else False

    @cached_property
    def company_share_id(self):
        return self._json_data.get("companyShareId")

    @cached_property
    def subgroup(self):
        return self._json_data.get("subGroup")

    @cached_property
    def scrip(self):
        return self._json_data.get("scrip")

    @cached_property
    def company_name(self):
        return self._json_data.get("companyName")

    @cached_property
    def share_type_name(self):
        return self._json_data.get("shareTypeName")

    @cached_property
    def share_group_name(self):
        return self._json_data.get("shareGroupName")

    @cached_property
    def status_name(self):
        return self._json_data.get("statusName")

    @cached_property
    def action(self):
        return self._json_data.get("action")

    @cached_property
    def issue_open_date(self):
        return self._json_data.get("issueOpenDate")

    @cached_property
    def issue_close_date(self):
        return self._json_data.get("issueCloseDate")


class UserSession:
    def __init__(self, account):
        self.account = account
        self.authorization = None
        self.branch_info = None
        self.set_user_session_defaults()

    def set_user_session_defaults(self):
        self.create_session()
        self.set_branch_info()

    def create_session(self):
        r = requests.post(
            'https://webbackend.cdsc.com.np/api/meroShare/auth/',
            json={
                'clientId': self.account.client_id,
                'username': self.account.username,
                'password': self.account.password
            }
        )

        if r.ok:
            self.authorization = r.headers['Authorization']
        else:
            raise ValueError('Unable to create session for %s' % self.account.username)

    def set_branch_info(self):
        bank = self.bank_info()
        r = requests.get(f"https://webbackend.cdsc.com.np/api/meroShare/bank/{bank['id']}",
                         headers=self.authorization_headers)
        if r.ok:
            self.branch_info = r.json()
        else:
            raise ValueError("Unable to fetch banks for user: %s" % self.account.name)

    def bank_info(self):
        r = requests.get('https://webbackend.cdsc.com.np/api/meroShare/bank/', headers=self.authorization_headers)
        if r.ok:
            banks = r.json()
            if len(banks) == 0:
                raise ValueError("No banks found for user: %s" % self.account.name)

            return banks[0]
        else:
            raise ValueError("Unable to fetch banks for user: %s" % self.account.name)

    @property
    def demat(self):
        return f"130{self.account.dp}{self.account.username}"

    @property
    def authorization_headers(self):
        return {
            'Authorization': self.authorization
        }

    def can_apply(self, company_share_id):
        response = requests.get(
            f"https://webbackend.cdsc.com.np/api/meroShare/applicantForm/customerType/{company_share_id}/{self.demat}",
            headers=self.authorization_headers).json()

        return True if response['message'] == "Customer can apply." else False

    def apply(self, number_of_shares, company_share_id):
        issues = self.open_issues()
        issue = next(
            (item for item in issues if item.is_unapplied_ordinary_share and item.company_share_id == company_share_id),
            None
        )

        if not issue:
            raise ValueError(f"UNAPPLIED ISSUE NOT FOUND!! -- {company_share_id}")

        if not self.can_apply(company_share_id):
            print(f"CANNOT APPLY!! -- {company_share_id}")
            return

        payload = {
            "demat": self.demat,
            "boid": self.account.username,
            "accountNumber": self.branch_info['accountNumber'],
            "customerId": self.branch_info['id'],
            "accountBranchId": self.branch_info['accountBranchId'],
            "appliedKitta": str(number_of_shares),
            "crnNumber": self.account.crn,
            "transactionPIN": self.account.pin,
            "companyShareId": str(company_share_id),
            "bankId": self.branch_info['bankId']
        }

        r = requests.post('https://webbackend.cdsc.com.np/api/meroShare/applicantForm/share/apply',
                          json=payload,
                          headers=self.authorization_headers)

        if r.ok:
            print(f"APPLIED SUCCESSFULLY!! -- {company_share_id}")
        else:
            print(f"APPLY UNSUCCESSFUL!! -- {company_share_id}")

    @cache
    def open_issues(self):
        payload = {
            "filterFieldParams": [
                {"key": "companyIssue.companyISIN.script", "alias": "Scrip"},
                {"key": "companyIssue.companyISIN.company.name", "alias": "Company Name"},
                {"key": "companyIssue.assignedToClient.name", "value": "", "alias": "Issue Manager"}
            ],
            "filterDateParams": [
                {"key": "minIssueOpenDate", "condition": "", "alias": "", "value": ""},
                {"key": "maxIssueCloseDate", "condition": "", "alias": "", "value": ""}
            ],
            "page": 1,
            "size": 20,
            "searchRoleViewConstants": "VIEW_APPLICABLE_SHARE"
        }

        r = requests.post('https://webbackend.cdsc.com.np/api/meroShare/companyShare/applicableIssue/',
                          json=payload, headers=self.authorization_headers)
        if r.ok:
            objects = r.json()['object']
            return [Issue(item) for item in objects]
        else:
            raise ValueError("Error while getting open issues!!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""MeroShare simplified for bulk actions.
    - Find currently open issues
    - Check issue status (applied, unapplied, allotted or not-allotted)"""
    )

    parser.add_argument('-r', '--report', action='store_true', help='Check IPO allotment reports')
    name_arg = parser.add_argument('-n', '--name',
                                   help='Name of the user, runs the script for this user only, default is run for '
                                        'all users in accounts.csv file')
    parser.add_argument('-a', '--apply', action='store_true', help='Apply to issues', default=False)
    share_id_arg = parser.add_argument('-id', '--company-share-id',
                                       help='Company share id to apply, required when -a/--apply flag is set', type=int)
    parser.add_argument('-s', '--shares', help='Number of shares to apply, default is 10', default=10)
    args = parser.parse_args()

    if args.report:
        print("Feature coming soon!!")
        exit(0)

    accounts = find_accounts_from_csv(args.name)

    for account in accounts:
        print("###################################################")
        print(f"####  %s  ####" % account.name.capitalize())
        print("###################################################")

        user = UserSession(account=account)

        if args.report:
            print("Feature coming soon!!")
        elif args.apply:
            if not args.company_share_id:
                raise argparse.ArgumentError(share_id_arg, "is required when -a/--apply flag is set, run the "
                                                           "script without any args to find the company share id")
            user.apply(args.shares, company_share_id=args.company_share_id)
        else:
            open_issues = user.open_issues()
            print(*open_issues, sep="\n")
