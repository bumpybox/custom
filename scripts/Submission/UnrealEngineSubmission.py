from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

# Integration UI
import imp
import os
imp.load_source(
    "IntegrationUI",
    os.path.join(
        RepositoryUtils.GetRepositoryPath("submission/Integration/Main", True),
        "IntegrationUI.py"
    )
)
import IntegrationUI

# Job Options UI
imp.load_source(
    "JobOptionsUI",
    os.path.join(
        RepositoryUtils.GetRepositoryPath("submission/Common/Main", True),
        "JobOptionsUI.py"
    )
)
import JobOptionsUI

########################################################################
# Globals
########################################################################
scriptDialog = None
settings = None

ProjectManagementOptions = ["Shotgun", "FTrack", "NIM"]
DraftRequested = False
jobOptions_dialog = None


########################################################################
# Main Function Called By Deadline
########################################################################
def __main__(*args):
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    global jobOptions_dialog

    scriptDialog = DeadlineScriptDialog()

    scriptDialog.SetTitle("Submit Unreal Engine Job To Deadline")
    scriptDialog.SetIcon(scriptDialog.GetIcon("UnrealEngine"))

    scriptDialog.AddTabControl("Tabs", 0, 0)

    scriptDialog.AddTabPage("Job Options")

    jobOptions_dialog = JobOptionsUI.JobOptionsDialog(
        parentAppName="UnrealEngineMonitor"
    )

    scriptDialog.AddScriptControl("JobOptionsDialog", jobOptions_dialog, "")

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid(
        "Separator1", "SeparatorControl", "Unreal Engine Options", 0, 0,
        colSpan=4
    )

    scriptDialog.AddControlToGrid("ProjectLabel", "LabelControl", "Project File", 1, 0, "The project to be rendered.", False)
    scriptDialog.AddSelectionControlToGrid("ProjectBox", "FileBrowserControl", "", "Unreal Project Files (*.uproject);;All Files (*)", 1, 1, colSpan=3)

    scriptDialog.AddControlToGrid("MapLabel", "LabelControl", "Game Map", 2, 0, "The path to the map that will be loaded for the render.", False)
    scriptDialog.AddControlToGrid("MapBox", "TextControl", "", 2, 1, colSpan=3)

    scriptDialog.AddControlToGrid("LevelSequenceLabel", "LabelControl", "Level Sequence", 3, 0, "The path to the level sequence that will be rendered out. eg. /Game/PathToSequence/SequenceName", False)
    scriptDialog.AddControlToGrid("LevelSequenceBox", "TextControl", "", 3, 1, colSpan=3)

    movieQueueCheckBox = scriptDialog.AddSelectionControlToGrid("MovieQueueCheckBox", "CheckBoxControl", True, "Movie Queue", 4, 0, "Submits render with Movie Queue.", True)
    movieQueueCheckBox.ValueModified.connect(MovieQueueCheckBoxChanged)
    movieQueueCheckBox.setChecked(False)
    movieQueueTextBox = scriptDialog.AddControlToGrid("MovieQueueTextBox", "TextControl", "", 4, 1, colSpan=3)
    movieQueueTextBox.setEnabled(False)

    scriptDialog.AddControlToGrid("FramesLabel", "LabelControl", "Frame List", 5, 0, "The list of frames to render.", False)
    scriptDialog.AddControlToGrid("FramesBox", "TextControl", "", 5, 1, colSpan=3)

    scriptDialog.AddControlToGrid("ChunkSizeLabel", "LabelControl", "Frames Per Task", 6, 0, "This is the number of frames that will be rendered at a time for each job task.", False)
    scriptDialog.AddRangeControlToGrid("ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 6, 1)

    scriptDialog.AddControlToGrid("VersionLabel", "LabelControl", "Version", 6, 2 , "The version of Unreal Engine to render with.", False)
    scriptDialog.AddComboControlToGrid("VersionBox", "ComboControl", "4", ("4", "5"), 6, 3)

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.AddTabPage("Output Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid("Separator2", "SeparatorControl", "Output Options", 0, 0, colSpan=4)

    scriptDialog.AddControlToGrid("OutputDirLabel", "LabelControl", "Output Directory", 1, 0,  "Destination folder for rendered images. Defaults to Project/Saved/Screenshots if left blank.", False)
    scriptDialog.AddSelectionControlToGrid("OutputDirBox", "FolderBrowserControl", "", "", 1, 1, colSpan=3)

    scriptDialog.AddControlToGrid("OutputNameLabel", "LabelControl", "Output File Naming", 2, 0, "Sets the naming format for the output files. Defaults to project.{frame}. Available Tokens {fps}, {frame}, {width}, {height}, {world}, {quality}, {material}", False)
    scriptDialog.AddControlToGrid("OutputNameBox", "TextControl", "", 2, 1, colSpan=3)

    scriptDialog.AddControlToGrid("OutputFormatLabel", "LabelControl", "Output Format", 3, 0, "The format for the output filename.", False)
    formatBox = scriptDialog.AddComboControlToGrid("OutputFormatBox", "ComboControl", "PNG", ("JPG", "BMP", "PNG", "AVI", "CustomRenderPasses"), 3, 1)
    formatBox.ValueModified.connect(OutputFormatModified)

    overrideResolutionBox = scriptDialog.AddSelectionControlToGrid("OverrideResolutionBox", "CheckBoxControl", False, "Override Resolution", 4, 0, "Enable to override render resolution.", True)
    overrideResolutionBox.ValueModified.connect(OverrideResolutionChanged)

    scriptDialog.AddControlToGrid("WidthLabel", "LabelControl", "Width", 5, 0, "Sets the output width in pixels.")
    scriptDialog.AddRangeControlToGrid("WidthBox", "RangeControl", 1920, 1, 32768, 0, 1, 5, 1)

    scriptDialog.AddControlToGrid("HeightLabel", "LabelControl", "Height", 5, 2, "Sets the output height in pixels.")
    scriptDialog.AddRangeControlToGrid("HeightBox", "RangeControl", 1080, 1, 32768, 0, 1, 5, 3)

    scriptDialog.AddControlToGrid("FrameRateLabel", "LabelControl", "Frame Rate", 6, 0, "Sets the frame rate of the output.")
    scriptDialog.AddRangeControlToGrid("FrameRateBox", "RangeControl", 30, 1, 120, 0, 1, 6, 1)

    scriptDialog.AddControlToGrid("MovieQualityLabel", "LabelControl", "Render Quality", 6, 2, "Sets the compression quality. Expressed in a percentage.")
    scriptDialog.AddRangeControlToGrid("MovieQualityBox", "RangeControl", 75, 1, 100, 0, 1, 6, 3)

    scriptDialog.AddControlToGrid("DelayBeforeLabel", "LabelControl", "Delay Before Warmup", 7, 0, "Number of frames to run the scene before playing the sequence. This will not play out in real-time.")
    scriptDialog.AddRangeControlToGrid("DelayBeforeBox", "RangeControl", 0, 0, 32768, 0, 1, 7, 1)

    scriptDialog.AddSelectionControlToGrid("CinematicModeBox", "CheckBoxControl", True, "Cinematic Mode", 7, 2, "Hides Player Character and disables Player Character Movement. Also disables HUD.", True)
    scriptDialog.AddSelectionControlToGrid("HideMessagesBox", "CheckBoxControl", True, "Hide Onscreen Messages", 7, 3, "Hides on screen messages like \"Rebuild Lighting\" or \"Pring String\" outputs.", True)

    scriptDialog.AddSelectionControlToGrid("EnableVSyncBox", "CheckBoxControl", True, "Enable VSync", 8, 0, "Enable VSync for batch rendering.", True)
    scriptDialog.AddSelectionControlToGrid("DisableTextureStreamingBox", "CheckBoxControl", True, "Disable Texture Streaming", 8, 1, "Disable Texture streaming while rendering. Will take longer to render, but worth it for final renders.", True)

    scriptDialog.AddControlToGrid("CustomRenderPassesLabel", "LabelControl", "Custom Render Passes", 9, 0, "")

    renderPasses = ("AmbientOcclusion", "BaseColor", "CustomDepth", "CustomDepthWorldUnits", "CustomStencil", "FinalImage", "MaterialAO", "Metallic", "Opacity", "PostTonemapHDRColor",
    "Roughness", "SceneColor", "SceneDepth", "SceneDepthWorldUnits", "SeparateTranslucencyA", "SeparateTranslucencyRGB", "ShadingModel", "Specular", "SubsurfaceColor", "WorldNormal")

    scriptDialog.AddComboControlToGrid("CustomRenderPassesBox", "MultiSelectListControl", "AmbientOcclusion", renderPasses, 9, 1, colSpan=3)

    captureHDRBox = scriptDialog.AddSelectionControlToGrid("CaptureHDRBox", "CheckBoxControl", True, "Capture Frames in HDR", 10, 0, "Renders with HDR in the .exr format.", True)
    captureHDRBox.ValueModified.connect(CaptureHDRChanged)

    scriptDialog.AddControlToGrid("HDRCompressionQualityLabel", "LabelControl", "HDR Compression Quality", 11, 0, "Compression Quality for HDR Frames (0 for no compression, 1 for default compression which can be slow).")
    scriptDialog.AddRangeControlToGrid("HDRCompressionQualityBox", "RangeControl", 0, 0, 1, 0, 1, 11, 1)

    scriptDialog.AddControlToGrid("CaptureGamutLabel", "LabelControl", "Capture Gamut", 11, 2, "")
    scriptDialog.AddComboControlToGrid("CaptureGamutBox", "ComboControl", "HCGM_Rec709", ("HCGM_Rec709", "HCGM_P3DCI", "HCGM_Rec2020", "HCGM_ACES", "HCGM_ACEScg", "HCGM_MAX"), 11, 3)

    scriptDialog.AddControlToGrid("PostProcessingLabel", "LabelControl", "Post Processing Material", 12, 0, "Custom Post Processing Material to use for rendering.", False)
    scriptDialog.AddControlToGrid("PostProcessingBox", "TextControl", "", 12, 1, colSpan=3)

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs(scriptDialog, "UnrealEngineMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False)

    scriptDialog.EndTabControl()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid("HSpacer1", 0, 0)
    submitButton = scriptDialog.AddControlToGrid("SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False)
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid("CloseButton", "ButtonControl", "Close", 0, 2, expand=False)
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    closeButton.ValueModified.connect(jobOptions_dialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ("ProjectBox", "MapBox", "LevelSequenceBox", "MovieQueueTextBox", "FramesBox", "ChunkSizeBox", "VersionBox", "OutputDirBox",
    "OutputNameBox", "OutputFormatBox", "OverrideResolutionBox", "WidthBox", "HeightBox", "FrameRateBox", "MovieQualityBox",
    "DelayBeforeBox", "CinematicModeBox", "HideMessagesBox", "EnableVSyncBox", "DisableTextureStreamingBox", "CustomRenderPassesBox",
    "CaptureHDRBox", "HDRCompressionQualityBox", "CaptureGamutBox", "PostProcessingBox")

    scriptDialog.LoadSettings(GetSettingsFilename(), settings)
    scriptDialog.EnabledStickySaving(settings, GetSettingsFilename())

    OverrideResolutionChanged(None)
    OutputFormatModified(None)

    scriptDialog.ShowDialog(False)


def GetSettingsFilename():
    return Path.Combine(
        ClientUtils.GetUsersSettingsDirectory(), "UnrealEngineSettings.ini"
    )


def OverrideResolutionChanged(*args):
    global scriptDialog
    overrideResolution = scriptDialog.GetValue("OverrideResolutionBox")
    scriptDialog.SetEnabled("WidthLabel", overrideResolution)
    scriptDialog.SetEnabled("WidthBox", overrideResolution)
    scriptDialog.SetEnabled("HeightLabel", overrideResolution)
    scriptDialog.SetEnabled("HeightBox", overrideResolution)


def OutputFormatModified(*args):
    global scriptDialog

    usingCustom = (
        scriptDialog.GetValue("OutputFormatBox") == "CustomRenderPasses"
    )

    scriptDialog.SetEnabled("CustomRenderPassesLabel", usingCustom)
    scriptDialog.SetEnabled("CustomRenderPassesBox", usingCustom)
    scriptDialog.SetEnabled("CaptureHDRBox", usingCustom)
    scriptDialog.SetEnabled("PostProcessingLabel", usingCustom)
    scriptDialog.SetEnabled("PostProcessingBox", usingCustom)

    CaptureHDRChanged(None)


def CaptureHDRChanged(*args):
    global scriptDialog

    capturingHDR = (
        scriptDialog.GetEnabled("CaptureHDRBox") and
        scriptDialog.GetValue("CaptureHDRBox")
    )

    scriptDialog.SetEnabled("HDRCompressionQualityLabel", capturingHDR)
    scriptDialog.SetEnabled("HDRCompressionQualityBox", capturingHDR)
    scriptDialog.SetEnabled("CaptureGamutLabel", capturingHDR)
    scriptDialog.SetEnabled("CaptureGamutBox", capturingHDR)


def MovieQueueCheckBoxChanged(*args):
    global scriptDialog

    state = scriptDialog.GetValue("MovieQueueCheckBox")

    invert_settings = [
        "LevelSequenceBox",
        "FramesBox",
        "ChunkSizeBox",
        "OutputDirBox",
        "OutputNameBox",
        "OutputFormatBox",
        "OutputFormatBox",
        "OverrideResolutionBox",
        "WidthBox",
        "HeightBox",
        "FrameRateBox",
        "MovieQualityBox",
        "DelayBeforeBox",
        "CinematicModeBox",
        "HideMessagesBox",
        "EnableVSyncBox",
        "DisableTextureStreamingBox",
    ]
    for setting in invert_settings:
        scriptDialog.SetEnabled(setting, not state)

    scriptDialog.SetEnabled("MovieQueueTextBox", state)


def IsMovie():
    global scriptDialog

    return (scriptDialog.GetValue("OutputFormatBox") == "AVI")


def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog
    global jobOptions_dialog

    warnings = []
    errors = []

    # Check if Unreal Engine project file(s) exist.
    sceneFile = scriptDialog.GetValue("ProjectBox").strip()
    if(not File.Exists(sceneFile)):
        errors.append("The Unreal Engine project file %s does not exist" % sceneFile)
    elif (not scriptDialog.GetValue("ProjectBox") and PathUtils.IsPathLocal(sceneFile)):
        warnings.append("The Unreal Engine project file %s is local. Are you sure you want to continue?" % sceneFile)

    mapPath = scriptDialog.GetValue("MapBox").strip()
    if len(mapPath) == 0:
        errors.append("Please specify a map to render.")

    levelSequence = scriptDialog.GetValue("LevelSequenceBox").strip()
    movieQueueCheckBox = scriptDialog.GetValue("MovieQueueCheckBox")
    movieQueueTextBox = scriptDialog.GetValue("MovieQueueTextBox").strip()
    if movieQueueCheckBox:
        if len(movieQueueTextBox) == 0:
            errors.append("Please specify a movie queue to render.")
    else:
        if len(levelSequence) == 0:
            errors.append("Please specify a level sequence to render.")

    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue("FramesBox")
    if not movieQueueCheckBox:
        if(not FrameUtils.FrameRangeValid(frames)):
            errors.append("Frame range %s is not valid" % frames)

    # Check output file.
    outputDir = scriptDialog.GetValue("OutputDirBox").strip()
    if not movieQueueCheckBox:
        if len(outputDir) == 0:
            warnings.append(
                "No output directory specified. All output will be created in "
                "the Project's default directory."
            )
        elif(not Directory.Exists(outputDir)):
            errors.append(
                "The directory of the output file {0} does not exist.".format(
                    outputDir
                )
            )
        elif(PathUtils.IsPathLocal(outputDir)):
            warnings.append(
                "The output file {0} is local. Are you sure you want to "
                "continue?".format(outputDir)
            )

    # Check if Integration options are valid.
    if not integration_dialog.CheckIntegrationSanity(outputDir):
        return

    if len(errors) > 0:
        scriptDialog.ShowMessageBox("The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % ("\n\n".join(errors)), "Errors")
        return

    if len(warnings) > 0:
        result = scriptDialog.ShowMessageBox("Warnings:\n\n%s\n\nDo you still want to continue?" % ("\n\n".join(warnings)), "Warnings", ("Yes", "No"))
        if result == "No":
            return

    jobOptions = jobOptions_dialog.GetJobOptionsValues()
    # Create job info file.
    jobInfoFilename = Path.Combine(ClientUtils.GetDeadlineTempPath(), "unreal_engine_job_info.job")
    writer = StreamWriter(jobInfoFilename, False, Encoding.Unicode)

    writer.WriteLine("Plugin=UnrealEngine")
    for option, value in jobOptions.iteritems():
        writer.WriteLine("%s=%s" % (option, value))

    if movieQueueCheckBox:
        writer.WriteLine("Frames=0")
    else:
        writer.WriteLine("Frames=%s" % frames)

    if IsMovie():
        writer.WriteLine("ChunkSize=100000")
    else:
        writer.WriteLine("ChunkSize=%s" % scriptDialog.GetValue("ChunkSizeBox"))

    if len(outputDir) > 0:
        writer.WriteLine("OutputDirectory0=%s" % (outputDir))

    # Integration
    extraKVPIndex = 0
    groupBatch = False

    if integration_dialog.IntegrationProcessingRequested():
        extraKVPIndex = integration_dialog.WriteIntegrationInfo(writer, extraKVPIndex)
        groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

    if groupBatch:
        writer.WriteLine("BatchName=%s\n" % (jobOptions["Name"]))
    writer.Close()

    # Create plugin info file.
    pluginInfoFilename = Path.Combine(ClientUtils.GetDeadlineTempPath(), "unreal_engine_plugin_info.job")
    writer = StreamWriter(pluginInfoFilename, False, Encoding.Unicode)

    writer.WriteLine("ProjectFile=%s" % sceneFile)
    writer.WriteLine("Version=%s" % scriptDialog.GetValue("VersionBox"))
    writer.WriteLine("Map=%s" % scriptDialog.GetValue("MapBox"))
    writer.WriteLine("Map=%s" % scriptDialog.GetValue("MapBox"))
    writer.WriteLine("LevelSequence=%s" % scriptDialog.GetValue("LevelSequenceBox"))
    writer.WriteLine("MovieQueue=%s" % scriptDialog.GetValue("MovieQueueTextBox"))
    writer.WriteLine("RenderMovieQueue=%s" % scriptDialog.GetValue("MovieQueueCheckBox"))
    writer.WriteLine("OverrideResolution=%s" % scriptDialog.GetValue("OverrideResolutionBox"))
    writer.WriteLine("ResX=%s" % scriptDialog.GetValue("WidthBox"))
    writer.WriteLine("ResY=%s" % scriptDialog.GetValue("HeightBox"))
    writer.WriteLine("VSyncEnabled=%s" % scriptDialog.GetValue("EnableVSyncBox"))
    writer.WriteLine("FrameRate=%s" % scriptDialog.GetValue("FrameRateBox"))
    writer.WriteLine("DisableTextureStreaming=%s" % scriptDialog.GetValue("DisableTextureStreamingBox"))
    writer.WriteLine("OutputDir=%s" % outputDir)
    writer.WriteLine("OutputFormat=%s" % scriptDialog.GetValue("OutputFormatBox"))
    writer.WriteLine("OutputQuality=%s" % scriptDialog.GetValue("MovieQualityBox"))
    writer.WriteLine("MovieName=%s" % scriptDialog.GetValue("OutputNameBox"))
    writer.WriteLine("CinematicMode=%s" % scriptDialog.GetValue("CinematicModeBox"))
    writer.WriteLine("WarmupFrames=%s" % scriptDialog.GetValue("DelayBeforeBox"))
    writer.WriteLine("HideMessages=%s" % scriptDialog.GetValue("HideMessagesBox"))

    writer.WriteLine("RenderPasses=%s" % ";".join(scriptDialog.GetValue("CustomRenderPassesBox")))
    writer.WriteLine("CaptureHDR=%s" % scriptDialog.GetValue("CaptureHDRBox"))
    writer.WriteLine("HDRCompressionQuality=%s" % scriptDialog.GetValue("HDRCompressionQualityBox"))
    writer.WriteLine("CaptureGamut=%s" % scriptDialog.GetValue("CaptureGamutBox"))
    writer.WriteLine("PostProcessingMaterial=%s" % scriptDialog.GetValue("PostProcessingBox"))

    writer.Close()

    # Setup the command line arguments.
    arguments = StringCollection()

    arguments.Add(jobInfoFilename)
    arguments.Add(pluginInfoFilename)

    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput(arguments)
    scriptDialog.ShowMessageBox(results, "Submission Results")
