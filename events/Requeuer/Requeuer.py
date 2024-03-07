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
        super().__init__()
        self.OnHouseCleaningCallback += self.OnHouseCleaning

    def Cleanup(self):
        del self.OnHouseCleaningCallback

    def OnHouseCleaning(self):
        method = RepositoryUtils.GetEventPluginConfigMetaDataDictionary
        self.plugin_metadata = method("Requeuer")
        print("Requeuer Event Plugin - On House Cleaning Started")

        configs = ["JobID1", "JobID2"]
        job_ids = [self.GetConfigEntryWithDefault(x, "") for x in configs]

        configs = ["RequeuePeriod1", "RequeuePeriod2"]
        periods = [self.GetConfigEntryWithDefault(x, "") for x in configs]
        for count, job_id in enumerate(job_ids):
            theJob = RepositoryUtils.GetJob(job_id, True)
            if not theJob:
                print("Could not find job with id: {}".format(job_id))

            RequeueThreshold = int(periods[count])
            print("Requeue Threshold in seconds:", RequeueThreshold)
            print("Job to requeue:", job_ids[count])

            now_time = datetime.now()
            now_time_str = datetime.strftime(now_time, '%Y-%m-%d %H:%M:%S.%f')
            metadata_entry = "LastRequeueTime{}".format(count)
            last_time_str = self.GetMetaDataEntry(metadata_entry)
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
                    if not self.plugin_metadata.ContainsKey(metadata_entry):
                        self.AddMetaDataEntry(metadata_entry, now_time_str)
                    else:
                        self.UpdateMetaDataEntry(metadata_entry, now_time_str)
            else:
                print("Wait Time between Requeues has not elapsed yet...")
