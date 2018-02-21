import os
import sys
import traceback
import re

from System.IO import *

from Deadline.Events import *
from Deadline.Jobs import *
from Deadline.Scripting import *

##############################################################################################
## This is the function called by Deadline to get an instance of the FTrack event listener.
##############################################################################################
def GetDeadlineEventListener():
    return FTrackEventListener()

def CleanupDeadlineEventListener( eventListener ):
    eventListener.Cleanup()

###############################################################
## The FTrack event listener class.
###############################################################
class FTrackEventListener (DeadlineEventListener):
    connected = False

    def __init__( self ):
        #TODO: Add suspended/resumed events?
        self.OnJobSubmittedCallback += self.OnJobSubmitted
        self.OnJobStartedCallback += self.OnJobStarted
        self.OnJobFinishedCallback += self.OnJobFinished
        self.OnJobRequeuedCallback += self.OnJobRequeued
        self.OnJobFailedCallback += self.OnJobFailed

    def ConfigureFTrack( self, ftrackUser="" ):
        #setup up env variables for FTrack
        ftrackURL = self.GetConfigEntryWithDefault( "FTrackURL", "" ).strip()
        ftrackKey = self.GetConfigEntryWithDefault( "FTrackAPIKey", "" ).strip()
        ftrackProxy = self.GetConfigEntryWithDefault( "FTrackProxy", "" ).strip()

        if ftrackUser:
            os.environ["LOGNAME"] = ftrackUser

        os.environ["FTRACK_SERVER"] = ftrackURL
        os.environ["FTRACK_APIKEY"] = ftrackKey

        if ftrackProxy:
            os.environ["FTRACK_PROXY"] = ftrackProxy

        if ftrackURL and ftrackKey:
            ftrackPath = Path.Combine( RepositoryUtils.GetAPISyncFolder(), "API" )

            if not os.path.exists( ftrackPath ):
                self.LogInfo( "ERROR: Could not find FTrack API at expected location '%s'" % ftrackPath )
                return False

            self.LogInfo( "Importing FTrack API from '%s'..." % ftrackPath )
            if not ftrackPath in sys.path:
                sys.path.append( ftrackPath )

            try:
                #do a test import
                import ftrack
                ftrack.setup( False )

                return True
            except:
                self.LogInfo( "An error occurred while trying to connect to FTrack:" )
                self.LogInfo( traceback.format_exc() )

        return False

    def Cleanup( self ):
        self.OnJobSubmittedCallback -= self.OnJobSubmitted
        self.OnJobStartedCallback -= self.OnJobStarted
        self.OnJobFinishedCallback -= self.OnJobFinished
        self.OnJobRequeuedCallback -= self.OnJobRequeued
        self.OnJobFailedCallback -= self.OnJobFailed

    def createComponents( self, job, assetVersion ):
        if job and assetVersion:
            frameList = job.FramesList 
            frameRangeOverride = job.GetJobExtraInfoKeyValue( "FrameRangeOverride" )
            if not frameRangeOverride == "" :
                if FrameUtils.FrameRangeValid( frameRangeOverride ):
                    frameList = frameRangeOverride
        
            if job.GetJobExtraInfoKeyValue( "FT_DraftUploadMovie" ).lower() == "true":
                for i in range( len(job.OutputDirectories) ):
                    outPath = os.path.normpath( job.OutputDirectories[i] )
                    outPath = RepositoryUtils.CheckPathMapping( outPath, True )

                    if i < len( job.OutputFileNames ):
                        outPath = os.path.join( outPath, job.OutputFileNames[i] )

                        #Change out our '#' padding for python-style padding, which FTrack expects
                        match = re.search( "#+", outPath )
                        if match:
                            padding = match.group( 0 )
                            outPath = "{0} [{1}]".format( outPath.replace( padding, "%%0%dd" % len(padding) ), frameList )

                    #If there is only a single output, then create a 'main' component name.
                    if job.GetJobExtraInfoKeyValue( "FT_DraftUploadMovie" ).lower() == "true":
                        componentName = self.GetConfigEntryWithDefault( "DraftMovieComponentName", "draft_movie" )
                        
                    elif len(job.OutputDirectories) == 1:
                        componentName = self.GetConfigEntryWithDefault( "MainComponentName", "main" )
                    else:
                        componentName = ("Deadline_Output_%d" % i)
                        
                    self.LogInfo( "Creating component '%s' for Deadline output '%s'..." % (componentName, outPath) )

                    if not File.Exists( outPath ):
                        raise Exception( "ERROR: component file is missing: %s" % outPath )
                    
                    if not os.access( outPath, os.R_OK ):
                        raise Exception( "ERROR: component file is unreadable: %s" % outPath )

                    try:
                        #Job's complete, so output should be present now, let FTrack pick a location for us
                        assetVersion.createComponent( name=componentName, path=outPath )
                    except:
                        #That failed =/
                        self.LogInfo( traceback.format_exc() )
                        self.LogInfo( "Failed to create component for output '%s'. No component will be created." % outPath )
            else:
                componentName = self.GetConfigEntryWithDefault( "DraftMovieComponentName", "draft_movie" )
                
                outputDirectories = job.JobOutputDirectories
                outputFilenames = job.JobOutputFileNames

                if len(outputFilenames) == 0:
                    raise Exception( "ERROR: Could not find an output path in Job properties, no movie will be uploaded to Shotgun." )
                
                # Just upload the first movie file if there is more than one.
                moviePath = Path.Combine( outputDirectories[0], outputFilenames[0] )
                moviePath = RepositoryUtils.CheckPathMapping( moviePath, True )
                moviePath = PathUtils.ToPlatformIndependentPath( moviePath )
                
                self.LogInfo( "Creating component '%s' for Draft output '%s'..." % (componentName, moviePath) )

                if not File.Exists( moviePath ):
                    raise Exception( "ERROR: movie file is missing: %s" % moviePath )
                
                if not os.access( moviePath, os.R_OK ):
                    raise Exception( "ERROR: movie file is unreadable: %s" % moviePath )

                try:
                    #Job's complete, so output should be present now, let FTrack pick a location for us
                    assetVersion.createComponent( name=componentName, path=moviePath )
                except:
                    #That failed =/
                    self.LogInfo( traceback.format_exc() )
                    self.LogInfo( "Failed to create component for output '%s'. No component will be created." % moviePath )
                
            
            uploadScene = job.GetJobExtraInfoKeyValue( "FT_UploadScene" )
            
            if uploadScene.lower() == "true":
                sceneFile = job.GetJobExtraInfoKeyValueWithDefault( "FT_Scene",self.GetDataFilename() )
                componentName = self.GetConfigEntryWithDefault( "SceneComponentName", "scene" )
                
                self.LogInfo( "Creating component '%s' for Scene '%s'..." % (componentName, sceneFile) )

                if not File.Exists( sceneFile ):
                    raise Exception( "ERROR: scene file is missing: %s" % sceneFile )
                
                if not os.access( sceneFile, os.R_OK ):
                    raise Exception( "ERROR: scene file is unreadable: %s" % sceneFile )

                try:
                    #Job's complete, so output should be present now, let FTrack pick a location for us
                    assetVersion.createComponent( name=componentName, path=sceneFile )
                except:
                    #That failed =/
                    self.LogInfo( traceback.format_exc() )
                    self.LogInfo( "Failed to create component for output '%s'. No component will be created." % sceneFile )
                
            self.LogInfo( "Done creating Components." )

    #Updates the FTrack version for a Job
    def updateVersionStatus( self, job, statusName, createComponents=False, createIfMissing=False ):
        try:
            if statusName:
                #Only do stuff if this job is tied to an FTrack Version/Project
                projectID = job.GetJobExtraInfoKeyValue( "FT_ProjectId" )
                versionID = job.GetJobExtraInfoKeyValue( "FT_VersionId" )
                username = job.GetJobExtraInfoKeyValue( "FT_Username" )

                if not versionID and createIfMissing:
                    #Creation process should properly set status
                    self.CreateFTrackVersion( job, createComponents=createComponents, initialStatus=statusName )
                elif projectID and versionID:
                    #Version already exists, we just need to update
                    success = self.ConfigureFTrack( username )

                    if success:
                        import ftrack

                        ft_project = ftrack.Project( id=projectID )
                        statuses = ft_project.getVersionStatuses()

                        #Need to find the status by name
                        ft_status = None
                        for status in statuses:
                            if status.getName().lower() == statusName.lower():
                                ft_status = status
                                break

                        ft_version = None
                        if ft_status == None:
                            self.LogInfo( "Could not find valid Version Status with name '%s'. Asset Version will not be updated." % statusName )
                        else:
                            self.LogInfo( "Updating FTrack Version to status '%s'..." % statusName )
                            ft_version = ftrack.AssetVersion( id=versionID )
                            ft_version.setStatus( ft_status )

                        if createComponents:
                            if not ft_version:
                                ft_version = ftrack.AssetVersion( id=versionID )

                            self.createComponents( job, ft_version )
        except:
            self.LogInfo( "An unexpected error occurred while update FTrack Asset Version status:" )
            self.LogInfo( traceback.format_exc() )

    def CreateFTrackVersion( self, job, createComponents=False, initialStatus=None ):
        versionID = None

        try:
            username = job.GetJobExtraInfoKeyValue( "FT_Username" )

            self.LogInfo( "Creating FTrack Version..." )
            success = self.ConfigureFTrack( username )

            if success:
                import ftrack
                ftrack.setup( False )

                projectID = job.GetJobExtraInfoKeyValue( "FT_ProjectId" )
                taskID = job.GetJobExtraInfoKeyValue( "FT_TaskId" )
                assetID = job.GetJobExtraInfoKeyValue( "FT_AssetId" )
                description = job.GetJobExtraInfoKeyValue( "FT_Description" )

                asset = ftrack.Asset( id=assetID )
                version = asset.createVersion( comment=description, taskid=taskID )

                if createComponents:
                    self.createComponents( job, version )

                #Set Version status based on the Deadline Job's status
                ftStatusName = ""
                dlStatus = job.Status
                if initialStatus:
                    ftStatusName = initialStatus
                else:
                    #Try to figure out what the status should be
                    if dlStatus == JobStatus.Active:
                        if job.RenderingChunks > 0:
                            ftStatusName = self.GetConfigEntryWithDefault( "VersionStatusStarted", "" ).strip()
                        else:
                            ftStatusName = self.GetConfigEntryWithDefault( "VersionStatusQueued", "" ).strip()
                    elif dlStatus == JobStatus.Failed:
                        ftStatusName = self.GetConfigEntryWithDefault( "VersionStatusFailed", "" ).strip()
                    elif dlStatus == JobStatus.Completed:
                        ftStatusName = self.GetConfigEntryWithDefault( "VersionStatusFinished", "" ).strip()

                if ftStatusName:
                    project = ftrack.Project( id=projectID )
                    statuses = project.getVersionStatuses()

                    ftStatus = None
                    for status in statuses:
                        if status.getName().lower() == ftStatusName.lower():
                            ftStatus = status
                            break

                    if ftStatus == None:
                        self.LogInfo( "Could not find valid Asset Version Status with name '%s'.  The Version Status might not be set properly." % ftStatusName )
                    else:
                        self.LogInfo( "Setting Asset Version to status '%s'." % ftStatusName )
                        version.setStatus( ftStatus )

                self.LogInfo( "Publishing new Version..." )
                version.publish()

                versionID = version.getId()
                self.LogInfo( "Successfully published new FTrack Asset Version with ID '{0}'".format( versionID ) )
                
                job.SetJobExtraInfoKeyValue( "FT_VersionId", str( versionID ) )
                job.ExtraInfo3 = str( version.getVersion() )
                RepositoryUtils.SaveJob( job )
                self.LogInfo( "Successfully saved updated Deadline Job." )
        except:
            self.LogInfo( "An unexpected error occurred while trying to create an Asset Version in FTrack:" )
            self.LogInfo( traceback.format_exc() )

        return versionID

    def updateThumbnail( self, job ):
        try:
            if len(job.JobOutputDirectories) == 0 or len(job.JobOutputFileNames) == 0:
                self.LogInfo( "Deadline is unaware of the output location; skipping thumbnail creation." )
            else:
                versionID = job.GetJobExtraInfoKeyValue( "FT_VersionId" )
                username = job.GetJobExtraInfoKeyValue( "FT_Username" )

                if versionID:
                    self.LogInfo( "Creating thumbnail...." )
                    success = self.ConfigureFTrack( username )

                    if success:
                        import ftrack

                        try:
                            ft_version = ftrack.AssetVersion( id=versionID )

                            #TODO: allow configuration of which frame to use (first, mid, last, custom)
                            frameList = job.JobFramesList 
                            frameRangeOverride = job.GetJobExtraInfoKeyValue( "FrameRangeOverride" )
                            if not frameRangeOverride == "":
                                inputFrameList = frameRangeOverride
                                frameList = FrameUtils.Parse( inputFrameList )
                                
                            thumbFrame = frameList[0]
                            paddedFilename = os.path.join( job.JobOutputDirectories[0], job.JobOutputFileNames[0] )

                            padding = StringUtils.GetNumeralKeyFromPath( paddedFilename, ['#', '?'], True )

                            if padding:
                                self.LogInfo( "padding found: " + padding )
                                framePath = StringUtils.ReplaceNumeralKey( paddedFilename, padding, thumbFrame, True )
                                self.LogInfo( "using path: " + framePath )
                                
                                if not File.Exists( framePath ):
                                    raise Exception( "ERROR: image file is missing: %s" % framePath )
                                
                                if not os.access( framePath, os.R_OK ):
                                    raise Exception( "ERROR: image file is unreadable: %s" % framePath )

                                thumb = ft_version.createThumbnail( framePath )
                                self.LogInfo( "done!" )
                            else:
                                self.LogInfo( "no padding...." )
                                #TODO: No padding, single frame
                                pass

                        except:
                            self.LogInfo( "An error occurred while trying to upload thumbnail to FTrack:" )
                            self.LogInfo( traceback.format_exc() )
        except:
            self.LogInfo( traceback.format_exc() )

    def OnJobSubmitted( self, job ):
        if self.isFTrackJob( job ):
            createOnSubmit = self.GetBooleanConfigEntryWithDefault( "CreateOnSubmission", True )

            if createOnSubmit:
                self.LogInfo( "FTrack metadata found, creating FTrack Asset Version..." )
                self.CreateFTrackVersion( job )

    def OnJobStarted( self, job ):
        if self.isFTrackJob( job ):
            createOnSubmit = self.GetBooleanConfigEntryWithDefault( "CreateOnSubmission", True )

            statusName = self.GetConfigEntryWithDefault( "VersionStatusStarted", "" ).strip()
            self.updateVersionStatus( job, statusName, createIfMissing=createOnSubmit )

    def OnJobFinished( self, job ):
        if self.isFTrackJob( job ):
            createOnSubmit = self.GetBooleanConfigEntryWithDefault( "CreateOnSubmission", True )

            versionID = job.GetJobExtraInfoKeyValue( "FT_VersionId" )

            statusName = self.GetConfigEntryWithDefault( "VersionStatusFinished", "" ).strip()
            self.updateVersionStatus( job, statusName, createComponents=True, createIfMissing=True )
            self.updateThumbnail( job )

    def OnJobRequeued( self, job ):
        if self.isFTrackJob( job ):
            createOnSubmit = self.GetBooleanConfigEntryWithDefault( "CreateOnSubmission", True )

            statusName = self.GetConfigEntryWithDefault( "VersionStatusQueued", "" ).strip()
            self.updateVersionStatus( job, statusName, createIfMissing=createOnSubmit )

    def OnJobFailed( self, job ):
        if self.isFTrackJob( job ):
            createOnSubmit = self.GetBooleanConfigEntryWithDefault( "CreateOnSubmission", True )

            statusName = self.GetConfigEntryWithDefault( "VersionStatusFailed", "" ).strip()
            self.updateVersionStatus( job, statusName, createIfMissing=createOnSubmit )

    #Determines whether or not this is a Job that we care about (ie, it has FTrack metadata)
    def isFTrackJob( self, job ):
        projectID = job.GetJobExtraInfoKeyValue( "FT_ProjectId" )
        taskID = job.GetJobExtraInfoKeyValue( "FT_TaskId" )
        assetID = job.GetJobExtraInfoKeyValue( "FT_AssetId" )

        if projectID and taskID and assetID:
            return True
        elif projectID or taskID or assetID:
            self.LogInfo( "ERROR: Incomplete FTrack Metadata.  FTrack Event Plugin requires at least FT_ProjectId, FT_TaskId, and FT_AssetId to be supplied in Extra Info KVPs." )

        return False
