import identifier
import scroll_util
import slack_util
import google_api
import channel_util

nag_pattern = r"nagjobs (tuesday|thursday)"


SHEET_ID = "1lPj9GjB00BuIq9GelOWh5GmiGsheLlowPnHLnWBvMOM"
eight_job_range = "House Jobs!A2:C25" # Format: Job Day Bro
fiftythree_job_range = "House Jobs!E2:G6"

# For matching purposes
tuesday = "tuesday"
thursday = "thursday"


class Job(object):
    def __init__(self, house, job_name, day, brother_name):
        self.house, self.job_name, self.day, self.brother_name = house, job_name, day, brother_name
        self.day = self.day.lower().strip()

    def lookup_brother_slack_id(self):
        brother_dict = scroll_util.find_by_name(self.brother_name)
        return identifier.lookup_brother_userids(brother_dict)


def nag_callback(slack, msg, match):
    # Only allow in command center
    if msg["channel"] != channel_util.COMMAND_CENTER_ID:
        response = channel_util.NOT_ALLOWED_HERE
    else:
        # Get the day
        day = match.group(1).lower()

        # Get the spreadsheet section
        eight_jobs = google_api.get_sheet_range(SHEET_ID, eight_job_range)
        ft_jobs = google_api.get_sheet_range(SHEET_ID, fiftythree_job_range)

        # Turn to job objects
        eight_jobs = [Job("8", *r) for r in eight_jobs]
        ft_jobs = [Job("53", *r) for r in ft_jobs]
        jobs = eight_jobs + ft_jobs

        # Filter to day
        jobs = [j for j in jobs if j.day == day]

        # Nag each
        response = "Do your jobs! They are as follows:\n"
        for job in jobs:
            response += "({}) {} -- ".format(job.house, job.job_name)
            ids = job.lookup_brother_slack_id()
            if ids:
                for id in ids:
                    response += "<@{}> ".format(id)
            else:
                response += "{} (scroll not found. Please register for @ notifications!)".format(job.brother_name)
            response += "\n"

    slack_util.reply(slack, msg, response, in_thread=False, to_channel=channel_util.GENERAL)
