# CyCierge Admin (Android)

1. Copy `php-api/admin/api/` to `<webroot>/cycierge/admin/api/` on the Pi.
2. Edit `app/src/main/java/com/cycierge/admin/Config.kt` (LAN IP, Tailscale URL, APP_PATH).
3. Open this folder in Android Studio -> sync -> Run, or:
     ./gradlew assembleDebug && adb install -r app/build/outputs/apk/debug/app-debug.apk
   (no gradlew yet? run `gradle wrapper --gradle-version 8.7` once, or let Android Studio create it)
4. Debug: adb logcat | grep -iE "okhttp|cycierge"
