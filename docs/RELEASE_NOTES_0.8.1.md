# EARTH UNLOCK v0.8.1

## Global app foundation
- Permanent Android application ID and namespace: `com.earthunlock.app`.
- Korean and English UI resources separated from app logic.
- App language can follow the device language or be selected manually in the app.
- Unsupported device languages fall back to English.
- Android 13+ per-app language settings list Korean and English.
- The selected language is stored independently from exploration data.

## Preserved behavior
- GPS foreground tracking and adaptive polling are unchanged.
- Local SQLite exploration records and map viewport logic are unchanged.
- Nickname profile remains local-only; Firebase synchronization and global leaderboard are not implemented yet.

## Build validation
- GitHub Actions static lifecycle checks passed.
- Kotlin unit tests passed.
- Release APK build passed.
- APK signing certificate verification passed.

## Important package migration note
The application ID changed from `com.example.earthexplorer` to `com.earthunlock.app`. Android treats this as a separate app. It can be installed alongside the old app, but Android will not automatically migrate the old app's local SQLite records or settings. Keep the old app installed until you decide whether its local exploration history is still needed. Future updates to `com.earthunlock.app` can install over this new package with the same signing key.
