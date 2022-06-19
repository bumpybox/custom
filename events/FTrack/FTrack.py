import os
import subprocess
import json

from Deadline.Events import DeadlineEventListener
from Deadline.Scripting import RepositoryUtils


def GetDeadlineEventListener():
    return FTrackEventListener()


def CleanupDeadlineEventListener(eventListener):
    eventListener.Cleanup()


class FTrackEventListener (DeadlineEventListener):
    connected = False

    def __init__(self):
        self.OnJobSubmittedCallback += self.OnJobSubmitted
        self.OnJobStartedCallback += self.OnJobStarted
        self.OnJobFinishedCallback += self.OnJobFinished
        self.OnJobRequeuedCallback += self.OnJobRequeued
        self.OnJobFailedCallback += self.OnJobFailed
        self.OnJobSuspendedCallback += self.OnJobSuspended
        self.OnJobResumedCallback += self.OnJobResumed

    def Cleanup(self):
        self.OnJobSubmittedCallback -= self.OnJobSubmitted
        self.OnJobStartedCallback -= self.OnJobStarted
        self.OnJobFinishedCallback -= self.OnJobFinished
        self.OnJobRequeuedCallback -= self.OnJobRequeued
        self.OnJobFailedCallback -= self.OnJobFailed
        self.OnJobSuspendedCallback -= self.OnJobSuspended
        self.OnJobResumedCallback -= self.OnJobResumed

    def load_environment(self, job):
        print("Loading environment from: \"{}\"".format(job))
        environment = {}
        if job.GetJobEnvironmentKeys():
            for key in job.GetJobEnvironmentKeys():
                value = job.GetJobEnvironmentKeyValue(key)
                environment[str(key)] = str(value)

        print(json.dumps(environment, indent=4))

        return environment

    def update_task_status(self, job, status_name):
        environment = {}

        # Setup environment
        if job.GetJobEnvironmentKeys():
            environment.update(self.load_environment(job))

        # If its a python job we need to set environment from dependencies.
        if job.JobPlugin.lower() == "python":
            for id in job.JobDependencyIDs:
                dependency = RepositoryUtils.GetJob(id, False)
                if dependency.GetJobEnvironmentKeys():
                    environment.update(self.load_environment(dependency))

        # Check environment has the variables needed.
        required_variables = [
            "AVALON_PROJECT", "AVALON_ASSET", "AVALON_TASK",
            "FTRACK_SERVER", "FTRACK_API_KEY", "FTRACK_API_USER"
        ]
        for variable in required_variables:
            if not environment.get(variable):
                print(
                    "Missing variable \"{}\" from environment.".format(
                        variable
                    )
                )
                return

            os.environ[variable] = environment[variable]

        # Its necessary to run the pype python executable to have the
        # ftrack_api module compatible.
        args = [
            "K:/python.bat",
            os.path.join(
                RepositoryUtils.GetEventPluginDirectory("FTrack"),
                "set_task_status.py"
            ),
            environment["AVALON_PROJECT"],
            environment["AVALON_ASSET"],
            environment["AVALON_TASK"],
            status_name
        ]
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            env=os.environ
        )

        output = proc.communicate()[0]

        if proc.returncode != 0:
            raise ValueError(
                "\"{}\" was not successful: {}".format(args, output)
            )

        print(output)

    def OnJobSubmitted(self, job):
        # Setting the environment does not work on job submitted so this is
        # handled in Pyblish when submitting to Deadline.
        pass

    def OnJobStarted(self, job):
        status_name = self.GetConfigEntryWithDefault(
            "VersionStatusStarted", ""
        ).strip()
        self.update_task_status(job, status_name)

    def OnJobFinished(self, job):
        # Check all jobs in batch are completed.
        batch_name = job.BatchName
        completed = True
        if batch_name:
            for repo_job in RepositoryUtils.GetJobs(True):
                if repo_job.BatchName == batch_name:
                    if repo_job.JobStatus.lower() != "completed":
                        completed = False
                        break

        if not completed:
            print(
                "Status update blocked, because not all jobs in batch \"{}\""
                " are completed.".format(batch_name)
            )
            return

        status_name = self.GetConfigEntryWithDefault(
            "VersionStatusFinished", ""
        ).strip()
        self.update_task_status(job, status_name)

    def OnJobRequeued(self, job):
        status_name = self.GetConfigEntryWithDefault(
            "VersionStatusQueued", ""
        ).strip()
        self.update_task_status(job, status_name)

    def OnJobFailed(self, job):
        status_name = self.GetConfigEntryWithDefault(
            "VersionStatusFailed", ""
        ).strip()
        self.update_task_status(job, status_name)

    def OnJobSuspended(self, job):
        status_name = self.GetConfigEntryWithDefault(
            "VersionStatusSuspended", ""
        ).strip()
        self.update_task_status(job, status_name)

    def OnJobResumed(self, job):
        status_name = self.GetConfigEntryWithDefault(
            "VersionStatusResumed", ""
        ).strip()
        self.update_task_status(job, status_name)
