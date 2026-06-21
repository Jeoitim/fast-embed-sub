Unicode true

# Target application details
!define APP_NAME "FastEmbedSub"
!ifndef APP_VERSION
  !define APP_VERSION "1.0.0"
!endif
!define APP_PUBLISHER "Jeoitim"
!define APP_WEBSITE "https://github.com/Jeoitim/fast-embed-sub"
!ifndef APP_DIST_DIR
  !define APP_DIST_DIR "outputs\main.dist"
!endif

Name "${APP_NAME}"

# Include Modern UI
!include "MUI2.nsh"

# Define installer file name
OutFile "outputs\FastEmbedSub_v${APP_VERSION}_Setup.exe"

# Default installation folder
InstallDir "$PROGRAMFILES64\FastEmbedSub"

# Registry key to check for directory (for updates)
InstallDirRegKey HKLM "Software\${APP_NAME}" ""

# Request application privileges for Windows Vista+
RequestExecutionLevel admin

# MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"

# Welcome page
!insertmacro MUI_PAGE_WELCOME
# Directory page
!insertmacro MUI_PAGE_DIRECTORY
# InstFiles page
!insertmacro MUI_PAGE_INSTFILES
# Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\FastEmbedSub.exe"
!insertmacro MUI_PAGE_FINISH

# Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

# Language Settings
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

# Installation Section
Section "Install"
  SetOutPath "$INSTDIR"
  
  # Copy all files recursively
  File /r "${APP_DIST_DIR}\*"

  # Write the installation path into the registry
  WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" "$INSTDIR"
  
  # Write the uninstall keys for Windows Control Panel Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" '"$INSTDIR\FastEmbedSub.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_WEBSITE}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1

  # Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"

  # Create Start Menu Shortcuts
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\FastEmbedSub.exe" "" "$INSTDIR\FastEmbedSub.exe" 0
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\卸载 ${APP_NAME}.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\assets\icon.ico" 0

  # Create Desktop Shortcut
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\FastEmbedSub.exe" "" "$INSTDIR\FastEmbedSub.exe" 0
SectionEnd

# Uninstaller Section
Section "Uninstall"
  # 安全检查：确保 $INSTDIR 不为空，且与注册表记录一致，防止误删用户重要目录
  StrCmp $INSTDIR "" error
  ReadRegStr $0 HKLM "Software\${APP_NAME}" "InstallDir"
  StrCmp $0 $INSTDIR registry_ok
  
error:
  Abort "卸载程序检测到安装目录非法或与注册表记录不一致 ($0 vs $INSTDIR)，停止卸载以保护文件安全。"
  
registry_ok:
  # 进一步确保主程序文件存在，防止误判
  IfFileExists "$INSTDIR\FastEmbedSub.exe" ok
  Abort "卸载程序未在当前目录找到 FastEmbedSub.exe，停止卸载以保护文件安全。"

ok:
  # Delete Shortcuts
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\卸载 ${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  Delete "$DESKTOP\${APP_NAME}.lnk"

  # Delete files and subfolders
  RMDir /r "$INSTDIR"

  # Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
  DeleteRegKey HKLM "Software\${APP_NAME}"
SectionEnd
