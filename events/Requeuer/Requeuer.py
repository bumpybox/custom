from __future__ import print_function, division
from datetime import datetime

from Deadline.Events import DeadlineEventListener
from Deadline.Scripting import RepositoryUtils


def GetDeadlineEventListener():
    return RequeuerEventListener()


def CleanupDeadlineEventListener(eventListener):
    eventListener.Cleanup()


class RequeuerEventListener(DeadlineEventListener):
    def __init__(self):
        self.OnHouseCleaningCallback += self.OnHouseCleaning

    def Cleanup(self):
        del self.OnHouseCleaningCallback

    def OnHouseCleaning(self):
        method = RepositoryUtils.GetEventPluginConfigMetaDataDictionary
        self.plugin_metadata = method("Requeuer")
        print("Requeuer Event Plugin - On House Cleaning Started")
        JobID = self.GetConfigEntryWithDefault("JobID", "")
        theJob = RepositoryUtils.GetJob(JobID, True)
        RequeueThreshold = self.GetIntegerConfigEntryWithDefault(
            "RequeuePeriod", 3600
        )
        print("Requeue Threshold in seconds:", RequeueThreshold)
        print("Job to requeue:", JobID)

        if theJob:
            now_time = datetime.now()
            now_time_str = datetime.strftime(now_time, '%Y-%m-%d %H:%M:%S.%f')
            last_time_str = self.GetMetaDataEntry("LastRequeueTime")
            if last_time_str is not None:
                last_time = datetime.strptime(
                    last_time_str, '%Y-%m-%d %H:%M:%S.%f'
                )
                up_time = now_time - last_time
                duration_in_s = up_time.total_seconds()
            else:
                duration_in_s = 100000
            print("Time in seconds since last requeue:", duration_in_s)
            if duration_in_s > RequeueThreshold:
                JobStatus = theJob.JobStatus
                if JobStatus == "Failed":
                    RepositoryUtils.ResumeFailedJob(theJob)
                else:
                    print("Requeueing Job!")
                    RepositoryUtils.RequeueJob(theJob)
                    if not self.plugin_metadata.ContainsKey("LastRequeueTime"):
                        self.AddMetaDataEntry("LastRequeueTime", now_time_str)
                    else:
                        self.UpdateMetaDataEntry(
                            "LastRequeueTime", now_time_str
                        )
            else:
                print("Wait Time between Requeues has not elapsed yet...")
        else:
            print("Job not found.")
