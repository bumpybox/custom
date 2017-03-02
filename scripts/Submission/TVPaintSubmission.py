from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

# For Draft Integration
import imp, os
imp.load_source( 'DraftIntegration', os.path.join( RepositoryUtils.GetRootDirectory(), "submission", "Draft", "Main", "DraftIntegration.py" ) )
from DraftIntegration import *

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
shotgunSettings = {}
fTrackSettings = {}
IntegrationOptions = ["Shotgun","FTrack"]

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global scriptDialog
    global settings

    dialogWidth = 600
    labelWidth = 150
    dialogHeight = 666
    controlWidth = 156

    tabWidth = dialogWidth-16
    tabHeight = 616

    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit TVPaint Job To Deadline" )
    scriptDialog.SetIcon( Path.Combine( RepositoryUtils.GetRootDirectory(), "plugins/TVPaint/TVPaint.ico" ) )

    scriptDialog.AddTabControl("Job Options Tabs", dialogWidth+8, tabHeight)

    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "" )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering. ", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render. " )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "TVPaint Options", 0, 0, colSpan=6 )

    scriptDialog.AddControlToGrid( "Job Mode", "LabelControl", "Job Mode", 1, 0, "The different TVPaint job modes supported by Deadline.", False )
    jobModeBox = scriptDialog.AddComboControlToGrid( "JobModeBox", "ComboControl", "Sequence/Animation", ("Sequence/Animation","Single Image","Script Job","Export Layers", "Single Layer"), 1, 1, colSpan=4)
    jobModeBox.ValueModified.connect(JobModeBoxChanged)

    scriptDialog.AddControlToGrid( "AlphaSaveModeLabel", "LabelControl", "Alpha Save Mode", 2, 0, "The different Alpha Save Mode's supported by TVPaint.", False )
    scriptDialog.AddComboControlToGrid( "AlphaSaveModeBox", "ComboControl", "NoPreMultiply", ("NoPreMultiply","PreMultiply","NoAlpha","AlphaOnly"), 2, 1, colSpan=4)

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "TVPaint File", 3, 0, "The TVPaint scene file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "TVPaint Files (*.tvpp);;All Files (*)", 3, 1, colSpan=5 )

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output File", 4, 0,  "The output path to render to.", False )
    outputBox = scriptDialog.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "", "QUICKTIME (*.mov);;AVI (*.avi);;BMP (*.bmp);;CINEON (*.cin);;DEEP (*.dip);;DPX (*.dpx);;FLI (*.fli);;GIF (*.gif);;ILBM (*.iff);;JPEG (*.jpg);;PCX (*.pcx);;PNG (*.png);;PSD (*.psd);;SGI (*.rgb);;SOFTIMAGE (*.pic);;SUN (*.ras);;TGA (*.tga);;TIFF (*.tiff);;VPB (*.vpb)", 4, 1, colSpan=5 )
    outputBox.ValueModified.connect(OutputBoxChanged)

    scriptDialog.AddControlToGrid( "ScriptLabel", "LabelControl", "Script File", 5, 0,  "The render script to use.", False )
    scriptDialog.AddSelectionControlToGrid( "ScriptBox", "FileBrowserControl", "", "George Scripts (*.grg);;All Files (*)", 5, 1, colSpan=5 )

    scriptDialog.AddControlToGrid( "LayerLabel", "LabelControl", "Layer Name", 6, 0,  "The layer to render.", False )
    scriptDialog.AddControlToGrid( "LayerBox", "TextControl", "", 6, 1, colSpan=5)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 7, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 7, 1, colSpan=5 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 8, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 8, 1, colSpan=4)

    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit TVPaint Scene File With Job", 8, 5, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering.", "" )

    scriptDialog.AddControlToGrid( "FrameNumberLabel", "LabelControl", "Frame Number", 9, 0, "This is the index number of the frame that will be rendered for the job task. ", False )
    scriptDialog.AddRangeControlToGrid( "FrameNumberBox", "RangeControl", 0, 0, 1000000, 0, 1, 9, 1, colSpan=4 )
    scriptDialog.AddSelectionControlToGrid( "UseCameraBox", "CheckBoxControl", False, "Use Scene Camera", 9, 5, "If this option is enabled, TVPaint only renders what's in the camera's frame.", "" )

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 10, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 10, 1, colSpan=3 )
    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 10, 4, "The version of TVPaint to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "11", ("11",), 10, 5)
    scriptDialog.EndGrid()

    scriptDialog.EndTabPage()


    scriptDialog.AddTabPage("Integration")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "Project Management", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "IntegrationLabel", "LabelControl", "Project Management", 1, 0, "", False )
    IntegrationTypeBox = scriptDialog.AddComboControlToGrid( "IntegrationTypeBox", "ComboControl", "Shotgun", IntegrationOptions, 1, 1, expand=False )
    IntegrationTypeBox.ValueModified.connect(IntegrationTypeBoxChanged)
    connectButton = scriptDialog.AddControlToGrid( "IntegrationConnectButton", "ButtonControl", "Connect...", 1, 2, expand=False )
    connectButton.ValueModified.connect(ConnectButtonPressed)
    createVersionBox = scriptDialog.AddSelectionControlToGrid( "CreateVersionBox", "CheckBoxControl", False, "Create new version", 1, 3, "If enabled, Deadline will connect to Shotgun/FTrack and create a new version for this job." )
    createVersionBox.ValueModified.connect(SubmitShotgunChanged)
    scriptDialog.SetEnabled( "CreateVersionBox", False )

    scriptDialog.AddControlToGrid( "IntegrationVersionLabel", "LabelControl", "Version", 2, 0, "The Shotgun/FTrack version name.", False )
    scriptDialog.AddControlToGrid( "IntegrationVersionBox", "TextControl", "", 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "IntegrationDescriptionLabel", "LabelControl", "Description", 3, 0, "The Shotgun/FTrack version description.", False )
    scriptDialog.AddControlToGrid( "IntegrationDescriptionBox", "TextControl", "", 3, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "IntegrationEntityInfoLabel", "LabelControl", "Selected Entity", 4, 0, "Information about the Shotgun/FTrack entity that the version will be created for.", False )
    entityInfoBox = scriptDialog.AddControlToGrid( "IntegrationEntityInfoBox", "MultiLineTextControl", "", 4, 1, colSpan=3 )
    entityInfoBox.ReadOnly = True

    scriptDialog.AddControlToGrid( "IntegrationDraftOptionsLabel", "LabelControl", "Draft Options", 5, 0, "Information about the Shotgun/FTrack entity that the version will be created for.", False )
    scriptDialog.AddSelectionControlToGrid( "IntegrationUploadMovieBox", "CheckBoxControl", False, "Create/Upload Movie", 5, 1, "If this option is enabled, a draft job will be created to upload a movie to shotgun." )
    scriptDialog.AddSelectionControlToGrid( "IntegrationUploadFilmStripBox", "CheckBoxControl", False, "Create/Upload Film Strip", 5, 2, "If this option is enabled, a draft job will be created to upload a filmstrip to shotgun." )
    scriptDialog.EndGrid()

    # Add Draft UI
    AddDraftUI( scriptDialog )

    SubmitShotgunChanged( None )
    SubmitDraftChanged( None )
    scriptDialog.EndTabPage()

    scriptDialog.EndTabControl()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","FrameNumberBox","ChunkSizeBox","VersionBox","SubmitSceneBox","UseCameraBox","OutputBox","BuildBox","JobModeBox","AlphaSaveModeBox","SubmitScriptBox","ScriptBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    LoadIntegrationSettings()
    updateDisplay()
    scriptDialog.SetValue("CreateVersionBox",False)

    OutputBoxChanged( None )
    JobModeBoxChanged( None )

    scriptDialog.ShowDialog( False )

def GetSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "TVPaintSettings.ini" )

def JobModeBoxChanged( *args ):
    global scriptDialog

    if scriptDialog.GetValue( "JobModeBox" ) == "Sequence/Animation" or scriptDialog.GetValue( "JobModeBox" ) == "Script Job":
        scriptDialog.SetEnabled( "ChunkSizeLabel", True)
        scriptDialog.SetEnabled( "ChunkSizeBox", True)
        scriptDialog.SetEnabled( "FramesLabel", True )
        scriptDialog.SetEnabled( "FramesBox", True)
        scriptDialog.SetEnabled( "FrameNumberLabel", False)
        scriptDialog.SetEnabled( "FrameNumberBox", False)
        scriptDialog.SetEnabled( "LayerLabel", False)
        scriptDialog.SetEnabled( "LayerBox", False)

    elif scriptDialog.GetValue( "JobModeBox" ) == "Export Layers":
        scriptDialog.SetEnabled( "ChunkSizeLabel", False)
        scriptDialog.SetEnabled( "ChunkSizeBox", False)
        scriptDialog.SetEnabled( "FramesLabel", False)
        scriptDialog.SetEnabled( "FramesBox", False)
        scriptDialog.SetEnabled( "FrameNumberLabel", False)
        scriptDialog.SetEnabled( "FrameNumberBox", False)
        scriptDialog.SetEnabled( "LayerLabel", False)
        scriptDialog.SetEnabled( "LayerBox", False)

    elif scriptDialog.GetValue( "JobModeBox" ) == "Single Image":
        scriptDialog.SetEnabled( "FrameNumberLabel", True)
        scriptDialog.SetEnabled( "FrameNumberBox", True)
        scriptDialog.SetEnabled( "ChunkSizeLabel", False)
        scriptDialog.SetEnabled( "ChunkSizeBox", False)
        scriptDialog.SetEnabled( "FramesLabel", False )
        scriptDialog.SetEnabled( "FramesBox", False)
        scriptDialog.SetEnabled( "LayerLabel", False)
        scriptDialog.SetEnabled( "LayerBox", False)

    if scriptDialog.GetValue( "JobModeBox" ) == "Single Layer":
        scriptDialog.SetEnabled( "ChunkSizeLabel", True)
        scriptDialog.SetEnabled( "ChunkSizeBox", True)
        scriptDialog.SetEnabled( "FramesLabel", True )
        scriptDialog.SetEnabled( "FramesBox", True)
        scriptDialog.SetEnabled( "FrameNumberLabel", False)
        scriptDialog.SetEnabled( "FrameNumberBox", False)
        scriptDialog.SetEnabled( "LayerLabel", True)
        scriptDialog.SetEnabled( "LayerBox", True)

    scriptDialog.SetEnabled( "ScriptLabel", (scriptDialog.GetValue( "JobModeBox" ) == "Script Job"))
    scriptDialog.SetEnabled( "ScriptBox", (scriptDialog.GetValue( "JobModeBox" ) == "Script Job") )

def OutputBoxChanged( *args ):
    global scriptDialog

    outputFile = scriptDialog.GetValue( "OutputBox" )
    isMovie = IsMovie( outputFile )
    enableAlphaSaveMode = bool(GetOutputFormat( outputFile ) in "AVI QUICKTIME TGA TIFF SGI ILBM SUN")

    if scriptDialog.GetValue( "JobModeBox" ) == "Sequence/Animation":
        scriptDialog.SetEnabled( "ChunkSizeLabel", not isMovie )
        scriptDialog.SetEnabled( "ChunkSizeBox", not isMovie)

    scriptDialog.SetEnabled( "AlphaSaveModeLabel", enableAlphaSaveMode)
    scriptDialog.SetEnabled( "AlphaSaveModeBox", enableAlphaSaveMode)

def IsMovie( outputFile ):
    return IsQt( outputFile ) or IsAVI( outputFile )

def IsQt( outputFile ):
    return outputFile.lower().endswith( ".mov" )

def IsAVI( outputFile ):
    return outputFile.lower().endswith( ".avi" )

def GetOutputFormat( outputFile ):
    global scriptDialog

    # Supported formats:
    if outputFile.lower().endswith( ".mov" ):
        return "QUICKTIME"
    if outputFile.lower().endswith( ".avi" ):
        return "AVI"
    if outputFile.lower().endswith( ".bmp" ):
        return "BMP"
    if outputFile.lower().endswith( ".cin" ):
        return "CINEON"
    if outputFile.lower().endswith( ".dip" ):
        return "DEEP"
    if outputFile.lower().endswith( ".dpx" ):
        return "DPX"
    if outputFile.lower().endswith( ".fli" ):
        return "FLI"
    if outputFile.lower().endswith( ".gif" ):
        return "GIF"
    if outputFile.lower().endswith( ".iff" ):
        return "ILBM"
    if outputFile.lower().endswith( ".jpg" ):
        return "JPEG"
    if outputFile.lower().endswith( ".pcx" ):
        return "PCX"
    if outputFile.lower().endswith( ".png" ):
        return "PNG"
    if outputFile.lower().endswith( ".psd" ):
        return "PSD"
    if outputFile.lower().endswith( ".rgb" ):
        return "SGI"
    if outputFile.lower().endswith( ".pic" ):
        return "SOFTIMAGE"
    if outputFile.lower().endswith( ".ras" ):
        return "SUN"
    if outputFile.lower().endswith( ".tga" ):
        return "TGA"
    if outputFile.lower().endswith( ".tiff" ):
        return "TIFF"
    if outputFile.lower().endswith( ".vpb" ):
        return "VPB"

    return "UNKNOWN"

def ConnectButtonPressed( *args ):
    global scriptDialog
    script = ""
    settingsName = ""
    usingShotgun = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun")

    if usingShotgun:
        script = Path.Combine( RepositoryUtils.GetRootDirectory(), "events/Shotgun/ShotgunUI.py" )
        settingsName = GetShotgunSettingsFilename()
    else:
        script = Path.Combine( RepositoryUtils.GetRootDirectory(), "submission/FTrack/Main/FTrackUI.py" )
        settingsName = GetFTrackSettingsFilename()

    args = ["-ExecuteScript", script, "TVPaintMonitor"]
    args += AdditionalArgs()

    output = ClientUtils.ExecuteCommandAndGetOutput( args )
    updated = ProcessLines( output.splitlines(), usingShotgun )
    if updated:
        File.WriteAllLines( settingsName, tuple(output.splitlines()) )
        updateDisplay()

def AdditionalArgs():
    usingShotgun = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun")
    additionalArgs = []

    if usingShotgun:
        if 'UserName' in shotgunSettings:
            userName = shotgunSettings['UserName']
            if userName != None and len(userName) > 0:
                additionalArgs.append("UserName="+str(userName))

        if 'VersionName' in shotgunSettings:
            versionName = shotgunSettings['VersionName']
            if versionName != None and len(versionName) > 0:
                additionalArgs.append("VersionName="+str(versionName))

        if 'TaskName' in shotgunSettings:
            taskName = shotgunSettings['TaskName']
            if taskName != None and len(taskName) > 0:
                additionalArgs.append("TaskName="+str(taskName))

        if 'ProjectName' in shotgunSettings:
            projectName = shotgunSettings['ProjectName']
            if projectName != None and len(projectName) > 0:
                additionalArgs.append("ProjectName="+str(projectName))

        if 'EntityName' in shotgunSettings:
            entityName = shotgunSettings['EntityName']
            if entityName != None and len(entityName) > 0:
                additionalArgs.append("EntityName="+str(entityName))

        if 'EntityType' in shotgunSettings:
            entityType = shotgunSettings['EntityType']
            if entityType != None and len(entityType) > 0:
                additionalArgs.append("EntityType="+str(entityType))

    else:
        if 'FT_Username' in fTrackSettings:
            userName = fTrackSettings['FT_Username']
            if userName != None and len(userName) > 0:
                additionalArgs.append("UserName="+str(userName))

        if 'FT_TaskName' in fTrackSettings:
            taskName = fTrackSettings['FT_TaskName']
            if taskName != None and len(taskName) > 0:
                additionalArgs.append("TaskName="+str(taskName))

        if 'FT_ProjectName' in fTrackSettings:
            projectName = fTrackSettings['FT_ProjectName']
            if projectName != None and len(projectName) > 0:
                additionalArgs.append("ProjectName="+str(projectName))

        if 'FT_AssetName' in fTrackSettings:
            assetName = fTrackSettings['FT_AssetName']
            if assetName != None and len(assetName) > 0:
                additionalArgs.append("AssetName="+str(assetName))


    return additionalArgs

def ProcessLines( lines, shotgun ):
    global shotgunSettings
    global fTrackSettings

    tempKVPs = {}

    for line in lines:
        line = line.strip()
        tokens = line.split( '=', 1 )

        if len( tokens ) > 1:
            key = tokens[0]
            value = tokens[1]
            tempKVPs[key] = value
    if len(tempKVPs)>0:
        if shotgun:
            shotgunSettings = tempKVPs
        else:
            fTrackSettings = tempKVPs
        return True
    return False

def updateDisplay():
    global fTrackSettings
    global shotgunSettings

    displayText = ""
    if scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun":
        if 'UserName' in shotgunSettings:
            displayText += "User Name: %s\n" % shotgunSettings[ 'UserName' ]
        if 'TaskName' in shotgunSettings:
            displayText += "Task Name: %s\n" % shotgunSettings[ 'TaskName' ]
        if 'ProjectName' in shotgunSettings:
            displayText += "Project Name: %s\n" % shotgunSettings[ 'ProjectName' ]
        if 'EntityName' in shotgunSettings:
            displayText += "Entity Name: %s\n" % shotgunSettings[ 'EntityName' ]
        if 'EntityType' in shotgunSettings:
            displayText += "Entity Type: %s\n" % shotgunSettings[ 'EntityType' ]
        if 'DraftTemplate' in shotgunSettings:
            displayText += "Draft Template: %s\n" % shotgunSettings[ 'DraftTemplate' ]

        scriptDialog.SetValue( "IntegrationEntityInfoBox", displayText )
        scriptDialog.SetValue( "IntegrationVersionBox", shotgunSettings.get( 'VersionName', "" ) )
        scriptDialog.SetValue( "IntegrationDescriptionBox", shotgunSettings.get( 'Description', "" ) )
    else:
        if 'FT_Username' in fTrackSettings:
            displayText += "User Name: %s\n" % fTrackSettings[ 'FT_Username' ]
        if 'FT_TaskName' in fTrackSettings:
            displayText += "Task Name: %s\n" % fTrackSettings[ 'FT_TaskName' ]
        if 'FT_ProjectName' in fTrackSettings:
            displayText += "Project Name: %s\n" % fTrackSettings[ 'FT_ProjectName' ]

        scriptDialog.SetValue( "IntegrationEntityInfoBox", displayText )
        scriptDialog.SetValue( "IntegrationVersionBox", fTrackSettings.get( 'FT_AssetName', "" ) )
        scriptDialog.SetValue( "IntegrationDescriptionBox", fTrackSettings.get( 'FT_Description', "" ) )

    if len(displayText)>0:
        scriptDialog.SetEnabled("CreateVersionBox",True)
        scriptDialog.SetValue("CreateVersionBox",True)
    else:
        scriptDialog.SetEnabled("CreateVersionBox",False)
        scriptDialog.SetValue("CreateVersionBox",False)

def LoadIntegrationSettings():
    global fTrackSettings
    global shotgunSettings
    fTrackSettings = {}
    shotgunSettings = {}

    settingsFile = GetShotgunSettingsFilename()
    if File.Exists( settingsFile ):
        ProcessLines( File.ReadAllLines( settingsFile ), True )

    settingsFile = GetFTrackSettingsFilename()
    if File.Exists( settingsFile ):
        ProcessLines( File.ReadAllLines( settingsFile ), False )

def IntegrationTypeBoxChanged():
    global scriptDialog
    updateDisplay()

    shotgunEnabled = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun") and scriptDialog.GetValue( "CreateVersionBox" )
    scriptDialog.SetEnabled( "IntegrationUploadMovieBox", shotgunEnabled )
    scriptDialog.SetEnabled( "IntegrationUploadFilmStripBox", shotgunEnabled )

def GetShotgunSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "TVPaintMonitorSettingsShotgun.ini" )

def GetFTrackSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "TVPaintMonitorSettingsFTrack.ini" )

def SubmitShotgunChanged( *args ):
    global scriptDialog

    integrationEnabled = scriptDialog.GetValue( "CreateVersionBox" )
    shotgunEnabled = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun")

    scriptDialog.SetEnabled( "IntegrationVersionLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationVersionBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationDescriptionLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationDescriptionBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationEntityInfoLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationEntityInfoBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationUploadMovieBox", integrationEnabled and shotgunEnabled )
    scriptDialog.SetEnabled( "IntegrationUploadFilmStripBox", integrationEnabled and shotgunEnabled )

def SubmitButtonPressed( *args ):
    global scriptDialog
    global shotgunSettings

    version = scriptDialog.GetValue( "VersionBox" )
    isScriptJob = bool(scriptDialog.GetValue( "JobModeBox" ) == "Script Job")
    scriptFile = scriptDialog.GetValue( "ScriptBox" ).strip()
    outputFile =""
    outputFormat =""
    frames =""

    # Check the TVPaint files.
    sceneFile = scriptDialog.GetValue( "SceneBox" ).strip()
    if( len( sceneFile ) == 0 ):
        scriptDialog.ShowMessageBox( "No TVPaint file specified", "Error" )
        return

    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "TVPaint file %s does not exist" % sceneFile, "Error" )
        return
    # If the submit scene box is checked check if they are local, if they are warn the user
    elif( not bool( scriptDialog.GetValue("SubmitSceneBox") ) and PathUtils.IsPathLocal( sceneFile ) ):
        result = scriptDialog.ShowMessageBox( "The TVPaint file " + sceneFile + " is local.\n\nAre you sure you want to continue?", "Warning", ("Yes","No") )
        if( result == "No" ):
            return

    # Check output file
    outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
    if len(outputFile) == 0:
        scriptDialog.ShowMessageBox( "Please specify an output file.", "Error" )
        return
    if(not Directory.Exists(Path.GetDirectoryName(outputFile))):
            scriptDialog.ShowMessageBox( "The directory of the output file %s does not exist." % Path.GetDirectoryName(outputFile), "Error" )
            return
    elif( PathUtils.IsPathLocal(outputFile) ):
        result = scriptDialog.ShowMessageBox( "The output file %s is local. Are you sure you want to continue?" % outputFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return

    outputFormat = GetOutputFormat( outputFile )
    if outputFormat == "UNKNOWN":
        scriptDialog.ShowMessageBox( "The output format is not supported. Valid formats are: \n "
                                        +"mov, avi, bmp, cin, dip, dpx, fli, gif, iff, jpg, pcx, png, psd, rgb, pic, ras, tga, tiff, vpb", "Error" )
        return
    elif outputFormat == "QUICKTIME":
        result = scriptDialog.ShowMessageBox( "Please note that, the export format '.mov(Quicktime)' is only available for 32bits version of TVPaint Animation. A different file format may generated if a different version of TVPaint is used.\n\nAre you sure you want to continue?", "Warning", ("Yes","No") )
        if( result == "No" ):
            return

    # Check if a valid frame range has been specified(if its a Sequence).
    if scriptDialog.GetValue( "JobModeBox" ) == "Sequence/Animation" or scriptDialog.GetValue( "JobModeBox" ) == "Script Job" or scriptDialog.GetValue( "JobModeBox" ) == "Single Layer":
        frames = scriptDialog.GetValue( "FramesBox" )
        if( not FrameUtils.FrameRangeValid( frames ) ):
            scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
            return
    else:
         frames = scriptDialog.GetValue( "FrameNumberBox" )

    # Check the TVPaint render script.
    if isScriptJob and len( scriptFile ) == 0:
        scriptDialog.ShowMessageBox( "'Script Job Mode' was selected but no custom render script was specified. Please specify custom script.", "Error" )
        return

    successes = 0
    failures = 0

    # Submit scene file
    jobName = scriptDialog.GetValue( "NameBox" )

    # Create job info file.
    jobInfoFilename = Path.Combine( GetDeadlineTempPath(), "tvpaint_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=TVPaint" )
    writer.WriteLine( "Name=%s" % jobName )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
    writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
    writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "ConcurrentTasksBox" ) )
    writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
    writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
    if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )

    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )

    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    elif len(outputFile) > 0:
        writer.WriteLine( "OutputFilename0=%s" % outputFile )

    writer.WriteLine( "Frames=%s" % frames )

    if IsMovie( outputFile ):
        writer.WriteLine( "ChunkSize=100000" )
    else:
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )



    #Shotgun
    extraKVPIndex = 0
    groupBatch = False
    if scriptDialog.GetValue( "CreateVersionBox" ):
        if scriptDialog.GetValue( "IntegrationTypeBox" ) == "Shotgun":
            writer.WriteLine( "ExtraInfo0=%s\n" % shotgunSettings.get('TaskName', "") )
            writer.WriteLine( "ExtraInfo1=%s\n" % shotgunSettings.get('ProjectName', "") )
            writer.WriteLine( "ExtraInfo2=%s\n" % shotgunSettings.get('EntityName', "") )
            writer.WriteLine( "ExtraInfo3=%s\n" % scriptDialog.GetValue( "IntegrationVersionBox" ) )
            writer.WriteLine( "ExtraInfo4=%s\n" % scriptDialog.GetValue( "IntegrationDescriptionBox" ) )
            writer.WriteLine( "ExtraInfo5=%s\n" % shotgunSettings.get('UserName', "") )

            for key in shotgunSettings:
                if key != 'DraftTemplate':
                    writer.WriteLine( "ExtraInfoKeyValue%d=%s=%s\n" % (extraKVPIndex, key, shotgunSettings[key]) )
                    extraKVPIndex += 1
            if scriptDialog.GetValue("IntegrationUploadMovieBox"):
                writer.WriteLine( "ExtraInfoKeyValue%s=Draft_CreateSGMovie=True\n" % (extraKVPIndex) )
                extraKVPIndex += 1
                groupBatch = True
            if scriptDialog.GetValue("IntegrationUploadFilmStripBox"):
                writer.WriteLine( "ExtraInfoKeyValue%s=Draft_CreateSGFilmstrip=True\n" % (extraKVPIndex) )
                extraKVPIndex += 1
                groupBatch = True
        else:
            writer.WriteLine( "ExtraInfo0=%s\n" % fTrackSettings.get('FT_TaskName', "") )
            writer.WriteLine( "ExtraInfo1=%s\n" % fTrackSettings.get('FT_ProjectName', "") )
            writer.WriteLine( "ExtraInfo2=%s\n" % scriptDialog.GetValue( "IntegrationVersionBox" ) )
            writer.WriteLine( "ExtraInfo4=%s\n" % scriptDialog.GetValue( "IntegrationDescriptionBox" ) )
            writer.WriteLine( "ExtraInfo5=%s\n" % fTrackSettings.get('FT_Username', "") )
            for key in fTrackSettings:
                writer.WriteLine( "ExtraInfoKeyValue%d=%s=%s\n" % (extraKVPIndex, key, fTrackSettings[key]) )
                extraKVPIndex += 1
    if groupBatch:
        writer.WriteLine( "BatchName=%s\n" % (jobName ) )
    writer.Close()

    # Create plugin info file.
    pluginInfoFilename = Path.Combine( GetDeadlineTempPath(), "tvpaint_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

    if( not bool(scriptDialog.GetValue( "SubmitSceneBox" )) ):
        writer.WriteLine( "SceneFile=%s" % sceneFile )

        if isScriptJob:
            writer.WriteLine( "ScriptFile=%s" % scriptFile )

    if outputFormat in "AVI QUICKTIME TGA TIFF SGI ILBM SUN":
        writer.WriteLine( "AlphaSaveModeBox=%s" % scriptDialog.GetValue( "AlphaSaveModeBox" ) )

    writer.WriteLine( "JobModeBox=%s" % scriptDialog.GetValue( "JobModeBox" ) )
    writer.WriteLine( "OutputFile=%s" % outputFile )
    writer.WriteLine( "Version=%s" % version )
    writer.WriteLine( "OutputFormat=%s" % outputFormat )
    writer.WriteLine( "UseCameraBox=%s" % scriptDialog.GetValue( "UseCameraBox" ) )

    writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
    writer.WriteLine( "Build0=None" )
    writer.WriteLine( "Build1=32bit" )
    writer.WriteLine( "Build2=64bit" )
    writer.WriteLine( "LayerName=%s" % scriptDialog.GetValue( "LayerBox" ) )

    writer.Close()

    # Setup the command line arguments.
    arguments = StringCollection()

    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( sceneFile )
        if isScriptJob:
            arguments.Add( scriptFile )

    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
