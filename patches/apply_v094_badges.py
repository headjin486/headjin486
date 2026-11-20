from pathlib import Path
import sys
root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"

(pkg / "BadgeManager.kt").write_text(r'''package com.earthunlock.app

import android.content.Context
import android.location.Geocoder
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.floor

data class ExplorerBadge(val id: String, val title: String, val description: String, val icon: String, val unlocked: Boolean)

object BadgeManager {
    private const val PREFS = "earth_unlock_badges"
    private fun prefs(context: Context) = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    // Called on the location service's background persistence executor.
    fun recordLocation(context: Context, lat: Double, lon: Double) {
        val p = prefs(context)
        val region = "${floor(lat * 10).toInt()}:${floor(lon * 10).toInt()}"
        val regions = p.getStringSet("regions", emptySet())?.toMutableSet() ?: mutableSetOf()
        if (regions.add(region)) p.edit().putStringSet("regions", regions).apply()

        val day = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())
        val days = p.getStringSet("days", emptySet())?.toMutableSet() ?: mutableSetOf()
        if (days.add(day)) p.edit().putStringSet("days", days).apply()

        // Reverse-geocode only after about 1 km of movement. Failure is harmless:
        // country recognition retries on a later accepted GPS fix.
        val oldLat = p.getFloat("country_check_lat", Float.NaN).toDouble()
        val oldLon = p.getFloat("country_check_lon", Float.NaN).toDouble()
        val moved = if (oldLat.isNaN() || oldLon.isNaN()) Double.POSITIVE_INFINITY
            else TrackMath.haversineMeters(oldLat, oldLon, lat, lon)
        if (moved >= 1000.0 || oldLat.isNaN()) {
            p.edit().putFloat("country_check_lat", lat.toFloat()).putFloat("country_check_lon", lon.toFloat()).apply()
            try {
                if (Geocoder.isPresent()) {
                    @Suppress("DEPRECATION")
                    val code = Geocoder(context, Locale.ENGLISH).getFromLocation(lat, lon, 1)
                        ?.firstOrNull()?.countryCode?.uppercase(Locale.ROOT)
                    if (!code.isNullOrBlank()) {
                        if (p.getString("home_country", null) == null) p.edit().putString("home_country", code).apply()
                        val countries = p.getStringSet("countries", emptySet())?.toMutableSet() ?: mutableSetOf()
                        if (countries.add(code)) p.edit().putStringSet("countries", countries).apply()
                    }
                }
            } catch (_: Exception) { /* Geocoder may be unavailable or offline. */ }
        }
    }

    fun badges(context: Context, store: TrackStore): List<ExplorerBadge> {
        val p = prefs(context)
        val km = store.distanceMeters() / 1000.0
        val area = store.exploredAreaSquareMeters() / 1_000_000.0
        val regions = p.getStringSet("regions", emptySet())?.size ?: 0
        val days = p.getStringSet("days", emptySet())?.size ?: 0
        val home = p.getString("home_country", null)
        val countries = p.getStringSet("countries", emptySet()) ?: emptySet()
        val foreign = if (home == null) 0 else countries.count { it != home }
        val explored = store.exploredCellCount() > 0
        return listOf(
            ExplorerBadge("first", "첫 발걸음", "처음으로 지도를 해금", "👣", explored),
            ExplorerBadge("km1", "산책가", "누적 1km 탐험", "🥾", km >= 1),
            ExplorerBadge("km10", "탐험가", "누적 10km 탐험", "🧭", km >= 10),
            ExplorerBadge("km50", "모험가", "누적 50km 탐험", "🏕️", km >= 50),
            ExplorerBadge("km100", "지구 여행자", "누적 100km 탐험", "🌍", km >= 100),
            ExplorerBadge("km500", "대탐험가", "누적 500km 탐험", "🚩", km >= 500),
            ExplorerBadge("area1", "안개 걷기", "누적 해금 면적 1km²", "🌤️", area >= 1),
            ExplorerBadge("area10", "새로운 세상", "누적 해금 면적 10km²", "🗺️", area >= 10),
            ExplorerBadge("area50", "영역 개척자", "누적 해금 면적 50km²", "🏅", area >= 50),
            ExplorerBadge("days3", "다시 걷기", "서로 다른 날 3일 탐험", "📅", days >= 3),
            ExplorerBadge("days7", "꾸준한 발걸음", "서로 다른 날 7일 탐험", "🗓️", days >= 7),
            ExplorerBadge("days30", "멈추지 않는 여정", "서로 다른 날 30일 탐험", "⏳", days >= 30),
            ExplorerBadge("region1", "새로운 지역", "첫 번째 탐험 구역 해금", "📍", regions >= 1),
            ExplorerBadge("region5", "지역 개척자", "서로 다른 5개 구역 해금", "🧭", regions >= 5),
            ExplorerBadge("region10", "대륙을 누비다", "서로 다른 10개 구역 해금", "🌐", regions >= 10),
            ExplorerBadge("country1", "첫 해외 탐험", "처음으로 고향 국가 밖의 지도 해금", "✈️", foreign >= 1),
            ExplorerBadge("country2", "국경을 넘어", "고향 국가 외 2개 국가 탐험", "🛫", foreign >= 2),
            ExplorerBadge("country5", "세계 탐험가", "고향 국가 외 5개 국가 탐험", "🌏", foreign >= 5)
        )
    }
}
''', encoding="utf-8")

service = pkg / "LocationTrackingService.kt"
s = service.read_text(encoding="utf-8")
anchor = "                                store.recordAndReveal(point, 12.0)\n                                lastSaved = loc\n"
if anchor not in s: raise SystemExit("v0.9.3 service persistence anchor missing")
s = s.replace(anchor, "                                store.recordAndReveal(point, 12.0)\n                                BadgeManager.recordLocation(this@LocationTrackingService, loc.latitude, loc.longitude)\n                                lastSaved = loc\n", 1)
service.write_text(s, encoding="utf-8")

activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")
anchor = "        panel.addView(row1); panel.addView(row2); panel.addView(privacy); root.addView(panel); setContentView(root)\n"
if anchor not in a: raise SystemExit("MainActivity panel anchor missing")
replacement = """        val badgesButton = Button(this).apply {
            text = "🏅  나의 배지"
            isAllCaps = false
            setOnClickListener { showBadges() }
        }
        panel.addView(row1); panel.addView(row2); panel.addView(privacy); panel.addView(badgesButton); root.addView(panel); setContentView(root)
"""
a = a.replace(anchor, replacement, 1)
anchor = "    private fun openAppSettings() {\n"
if anchor not in a: raise SystemExit("openAppSettings anchor missing")
method = """    private fun showBadges() {
        val badges = BadgeManager.badges(this, store)
        val unlocked = badges.count { it.unlocked }
        val lines = badges.joinToString("\\n\\n") { badge ->
            val mark = if (badge.unlocked) "✓" else "🔒"
            val title = if (badge.unlocked) badge.title else "???"
            "$mark  ${badge.icon}  $title\\n     ${badge.description}"
        }
        val content = TextView(this).apply {
            text = "획득한 배지  $unlocked / ${badges.size}\\n\\n$lines"
            textSize = 15f
            setTextColor(Color.WHITE)
            setPadding(28, 20, 28, 20)
            setLineSpacing(2f, 1.05f)
        }
        val scroll = android.widget.ScrollView(this).apply { addView(content) }
        AlertDialog.Builder(this).setTitle("🏅 나의 탐험 배지")
            .setView(scroll).setPositiveButton("닫기", null).show()
    }

"""
a = a.replace(anchor, method + anchor, 1)
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 47' not in g or 'versionName = "0.9.3"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 47', 'versionCode = 48', 1).replace('versionName = "0.9.3"', 'versionName = "0.9.4"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace("versionCode = 47", "versionCode = 48").replace('versionName = "0.9.3"', 'versionName = "0.9.4"')
v += """
# v0.9.4 local-first explorer badges.
grep -F 'BadgeManager.recordLocation' app/src/main/java/com/earthunlock/app/LocationTrackingService.kt >/dev/null
grep -F 'private fun showBadges()' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'ExplorerBadge("country1"' app/src/main/java/com/earthunlock/app/BadgeManager.kt >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.9.4 badge system patch applied")
