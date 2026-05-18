on run argv
  if (count of argv) < 3 then
    error "Usage: osascript send_imessage.applescript <target> <message> <image_path>"
  end if

  set targetNumber to item 1 of argv
  set messageBody to item 2 of argv
  set imagePath to item 3 of argv
  set imageFile to (POSIX file imagePath) as alias

  tell application "Messages"
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy targetNumber of targetService

    -- Send attachment first; this is more reliable than text-first on macOS Messages AppleScript.
    send imageFile to targetBuddy
    delay 1.2
    send messageBody to targetBuddy
  end tell
end run
