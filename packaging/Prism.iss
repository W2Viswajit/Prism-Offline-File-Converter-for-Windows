#ifndef BuildDir
  #error BuildDir must point to the PyInstaller Prism folder
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif
[Setup]
AppId={{8DE6833D-508A-4456-A872-BB656653B437}
AppName=Prism
AppVersion=0.1.3
AppPublisher=Viswajit
DefaultDirName={localappdata}\Programs\Prism
DefaultGroupName=Prism
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename=Prism-0.1.3-Setup-x64
SetupIconFile=..\prism.ico
UninstallDisplayIcon={app}\Prism.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
Name: "explorer"; Description: "Add Open with Prism to Explorer's classic right-click menu"; Flags: unchecked
[Files]
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Prism"; Filename: "{app}\Prism.exe"
Name: "{autodesktop}\Prism"; Filename: "{app}\Prism.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\Prism.exe"; Description: "Launch Prism"; Flags: nowait postinstall skipifsilent
[Registry]
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.png\shell\Prism.Installed"; ValueType: string; ValueName: ""; ValueData: "Open with Prism"; Tasks: explorer; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.png\shell\Prism.Installed"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Prism.exe"; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.png\shell\Prism.Installed\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Prism.exe"" ""%1"""; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpg\shell\Prism.Installed"; ValueType: string; ValueName: ""; ValueData: "Open with Prism"; Tasks: explorer; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpg\shell\Prism.Installed"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Prism.exe"; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpg\shell\Prism.Installed\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Prism.exe"" ""%1"""; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpeg\shell\Prism.Installed"; ValueType: string; ValueName: ""; ValueData: "Open with Prism"; Tasks: explorer; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpeg\shell\Prism.Installed"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Prism.exe"; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpeg\shell\Prism.Installed\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Prism.exe"" ""%1"""; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.webp\shell\Prism.Installed"; ValueType: string; ValueName: ""; ValueData: "Open with Prism"; Tasks: explorer; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.webp\shell\Prism.Installed"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Prism.exe"; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.webp\shell\Prism.Installed\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Prism.exe"" ""%1"""; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.bmp\shell\Prism.Installed"; ValueType: string; ValueName: ""; ValueData: "Open with Prism"; Tasks: explorer; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.bmp\shell\Prism.Installed"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Prism.exe"; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.bmp\shell\Prism.Installed\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Prism.exe"" ""%1"""; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tif\shell\Prism.Installed"; ValueType: string; ValueName: ""; ValueData: "Open with Prism"; Tasks: explorer; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tif\shell\Prism.Installed"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Prism.exe"; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tif\shell\Prism.Installed\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Prism.exe"" ""%1"""; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tiff\shell\Prism.Installed"; ValueType: string; ValueName: ""; ValueData: "Open with Prism"; Tasks: explorer; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tiff\shell\Prism.Installed"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Prism.exe"; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tiff\shell\Prism.Installed\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Prism.exe"" ""%1"""; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Prism.Installed"; ValueType: string; ValueName: ""; ValueData: "Open with Prism"; Tasks: explorer; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Prism.Installed"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Prism.exe"; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Prism.Installed\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Prism.exe"" ""%1"""; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\Prism.Installed"; ValueType: string; ValueName: ""; ValueData: "Open with Prism"; Tasks: explorer; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\Prism.Installed"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Prism.exe"; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\Prism.Installed\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Prism.exe"" ""%1"""; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.docx\shell\Prism.Installed"; ValueType: string; ValueName: ""; ValueData: "Open with Prism"; Tasks: explorer; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.docx\shell\Prism.Installed"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Prism.exe"; Tasks: explorer
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.docx\shell\Prism.Installed\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Prism.exe"" ""%1"""; Tasks: explorer

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var Exts: TArrayOfString; I: Integer; Key, Owner: String;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('explorer') then begin
    Exts := ['png','jpg','jpeg','webp','bmp','tif','tiff','pdf','txt','docx'];
    for I := 0 to GetArrayLength(Exts)-1 do begin
      Key := 'Software\Classes\SystemFileAssociations\.' + Exts[I] + '\shell\Prism.Open';
      if RegQueryStringValue(HKCU, Key, 'PrismOwner', Owner) and (Owner = 'PrismWindowsSourceApp') then
        RegDeleteKeyIncludingSubkeys(HKCU, Key);
    end;
  end;
end;
