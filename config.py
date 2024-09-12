import argparse

class Config:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--driver_path", type=str, help="The path to the chromedriver")
        parser.add_argument("--username", type=str, help="Your YZU student ID")
        parser.add_argument("--password", type=str, help="Your YZU password")
        parser.add_argument("--receiver_email", type=str)
        parser.add_argument("--sender_email", type=str, help="Please provide a gmail account")
        parser.add_argument("--sender_password", type=str, help="Please provide the gmail PAT")

        self.args = parser.parse_args()