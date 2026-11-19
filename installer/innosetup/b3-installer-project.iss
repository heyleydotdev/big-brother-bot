; Inno Setup script for the B3 2.x windows build.
;
; The input is the PyInstaller bundle built by the release workflow:
;   dist\b3_run\  (b3_run.exe, _internal\, conf\, sql\, plugins\, ...)
;
; Compile with the version taken from the git tag:
;   iscc /DB3_VERSION=2.0.1 installer\innosetup\b3-installer-project.iss
;
; Per user install (no admin): B3 writes its log and configuration next to the
; executable, which would not be allowed under Program Files.

#ifndef B3_VERSION
  #define B3_VERSION "0.0.0"
#endif

#define B3_BUILD_PATH "..\..\dist\b3_run"

[Setup]
AppId=5FB180C6-A3B3-46CF-85E0-F00168F1569C
AppName=BigBrotherBot
AppVersion={#B3_VERSION}
AppVerName=BigBrotherBot {#B3_VERSION}
AppPublisher=BigBrotherBot community continuation
AppPublisherURL=https://github.com/heyleydotdev/big-brother-bot
AppSupportURL=https://github.com/heyleydotdev/big-brother-bot/issues
AppCopyright=GNU GPL v2 or later
DefaultDirName={localappdata}\BigBrotherBot
DefaultGroupName=BigBrotherBot
DisableProgramGroupPage=yes
DisableStartupPrompt=yes
PrivilegesRequired=none
OutputDir=..\..\dist
OutputBaseFilename=b3-{#B3_VERSION}-windows-x64-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets_common\b3.ico
LicenseFile=..\..\LICENSE
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\b3_run.exe

[Files]
; user configuration survives an uninstall, everything else is removed
Source: "{#B3_BUILD_PATH}\*"; DestDir: "{app}"; Excludes: "conf\*"; Flags: recursesubdirs createallsubdirs
Source: "{#B3_BUILD_PATH}\conf\*"; DestDir: "{app}\conf"; Flags: recursesubdirs createallsubdirs uninsneveruninstall

[Icons]
Name: "{group}\BigBrotherBot"; Filename: "{app}\b3_run.exe"; WorkingDir: "{app}"
Name: "{group}\Configuration folder"; Filename: "{app}\conf"
Name: "{group}\Uninstall BigBrotherBot"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\b3_run.exe"; Description: "Run BigBrotherBot now"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
