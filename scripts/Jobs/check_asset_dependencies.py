import os

from Deadline.Scripting import MonitorUtils


def __main__():
    """Monitor based job script to copy selected job ids
    to the system clipboard."""
    selected_jobs = MonitorUtils.GetSelectedJobs()

    missing_files = []
    if selected_jobs:
        for job in selected_jobs:
            for dependency in job.RequiredAssets:
                if not os.path.exists(dependency.FileName):
                    missing_files.append(dependency.FileName)

    if missing_files:
        print("Missing files:\n{}".format("\n".join(missing_files)))
    else:
        print("All asset dependencies exist!")
