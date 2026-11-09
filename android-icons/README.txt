CyCierge Android icons - pick ONE option (option-cy OR option-lock).

From the repo root, in PowerShell (example uses the lock; swap "option-lock" for "option-cy"):

  Copy-Item .\android-icons\option-lock\res -Destination .\android-admin\app\src\main -Recurse -Force

Then point the manifest at the icon (run once):

  $f = ".\android-admin\app\src\main\AndroidManifest.xml"
  (Get-Content $f -Raw) -replace '<application\s+android:label','<application android:icon="@mipmap/ic_launcher" android:roundIcon="@mipmap/ic_launcher_round" android:label' | Set-Content $f -NoNewline

Rebuild and reinstall. If the old icon still shows, uninstall the app once or restart the launcher.
minSdk is 26, so these adaptive icons are all that is needed (no PNG mipmaps).
Includes a monochrome layer for Android 13+ themed icons.
