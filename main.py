import csv
import os
import argparse
import requests
import constants
from functools import cache, cached_property


def find_accounts_from_csv():
    acs = []
    with open(constants.ACCOUNTS_CSV_PATH, newline='') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            acs.append(
                Account(row['name'], row['dp'], row['username'], row['password'], row['crn'], row['pin'])
            )

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
        return ("""{name} - {subgroup} ({symbol}) - {share_type} ({share_group})
{open_date} - {close_date}{sep}{status}{sep}""".format(sep=os.linesep,
                                                       name=self.company_name,
                                                       subgroup=self.subgroup,
                                                       symbol=self.scrip,
                                                       open_date=self.issue_open_date,
                                                       close_date=self.issue_close_date,
                                                       share_type=self.share_type_name,
                                                       share_group=self.share_group_name,
                                                       status=self.status.capitalize()))

    @property
    def is_unapplied_ordinary_ipo(self):
        return self.is_ipo and self.is_ordinary_shares and not self.is_applied

    @property
    def is_ipo(self):
        return True if self.share_type_name == 'IPO' else False

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
    def sub_group(self):
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
        r = requests.get(f"https://webbackend.cdsc.com.np/api/meroShare/bank/{bank['id']}", headers=self.authorization_headers)
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
        response = requests.get(f"https://webbackend.cdsc.com.np/api/meroShare/applicantForm/customerType/{company_share_id}/{self.demat}",
                                headers=self.authorization_headers).json()

        return True if response['message'] == "Customer can apply." else False

    def unapplied_issues(self):
        return [issue for issue in self.open_issues() if issue.is_unapplied_ordinary_ipo]

    def apply_latest(self, number_of_shares):
        issues = self.unapplied_issues()

        if len(issues) == 0:
            print(f"NO ISSUES LEFT TO APPLY!! -- {self.account.name}")
            return

        self.apply(number_of_shares, issues[0])

    def apply_to_all(self, number_of_shares):
        issues = self.unapplied_issues()

        if len(issues) == 0:
            print(f"NO ISSUES LEFT TO APPLY!! -- {self.account.name}")
            return

        for issue in issues:
            self.apply(number_of_shares, issue)

    def apply(self, number_of_shares,  issue):
        if not self.can_apply(issue.company_share_id):
            print(f"CANNOT APPLY!! -- {issue.company_name}")
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
            "companyShareId": str(issue.company_share_id),
            "bankId": self.branch_info['bankId']
        }

        r = requests.post('https://webbackend.cdsc.com.np/api/meroShare/applicantForm/share/apply', json=payload, headers=self.authorization_headers)

        if r.ok:
            print(f"APPLIED SUCCESSFULLY!! -- {issue.company_name}")
        else:
            print(f"APPLY UNSUCCESSFUL!! -- {issue.company_name}")

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
    - Find open issues
    - Check applied issue
    - Check IPO allotments"""
    )

    parser.add_argument('-o', action='store_true', help='find currently open issues')
    parser.add_argument('-a', action='store_true', help='apply to all unapplied, default is apply to the latest one', default=False)
    parser.add_argument('-n', help='number of shares to apply', default=constants.SHARES)
    args = parser.parse_args()

    accounts = find_accounts_from_csv()

    for account in accounts:
        print("###################################################")
        print(f"####  %s  ####" % account.name.capitalize())
        print("###################################################")

        user = UserSession(account=account)

        if args.o:
            open_issues = user.open_issues()
            print(*open_issues, sep="\n")
        elif args.a:
            user.apply_to_all(args.n)
        else:
            user.apply_latest(args.n)
