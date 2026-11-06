# CyCierge Admin (Android)

1. Copy `php-api/admin/api/` to `<webroot>/cycierge/admin/api/` on the Pi.
2. Edit `app/src/main/java/com/cycierge/admin/Config.kt` (LAN IP, Tailscale URL, APP_PATH).
3. Open this folder in Android Studio -> sync -> Run, or:
     ./gradlew assembleDebug && adb install -r app/build/outputs/apk/debug/app-debug.apk
   (no gradlew yet? run `gradle wrapper --gradle-version 8.7` once, or let Android Studio create it)
4. Debug: adb logcat | grep -iE "okhttp|cycierge"

Connection: on the Pi's Wi-Fi subnet the app tries LAN first (1.5 s probe), anywhere else Funnel first (8 s probe);
the other route is always the fallback, and the route is re-probed on every network change. The chip in the app
shows LAN / REMOTE / OFFLINE, and a failed probe says why, e.g. "Pi unreachable - Funnel: HTTP 404; LAN: timeout".
