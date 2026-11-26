"""MY EARTH v0.10.46 - map-first dashboard (A), applied after v0.10.45."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

root = Path(sys.argv[1] if len(sys.argv) > 1 else "source")
main = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
original = main.read_text(encoding="utf-8")
s = original

def once(old, new):
    global s
    assert s.count(old) == 1, f"Expected exactly one anchor: {old[:100]}"
    s = s.replace(old, new, 1)

def block(start, end, new):
    global s
    a = s.index(start)
    b = s.index(end, a)
    s = s[:a] + new + s[b:]

once("    private lateinit var countText: TextView\n", """    private lateinit var countText: TextView
    private lateinit var percentText: TextView
    private lateinit var recordActionButton: Button
    private var startRequestedAt = 0L
    private val dashboardHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private val dashboardStatusPoll = object : Runnable {
        override fun run() {
            refreshTrackingStatus()
            dashboardHandler.postDelayed(this, 500L)
        }
    }
""")

block("        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setBackgroundColor", "        map = MapView(this).apply {", """        val navy = Color.rgb(13, 25, 38)
        val lime = Color.rgb(177, 235, 111)
        val config = resources.configuration
        val sidePanel = config.screenWidthDp >= 560 && config.screenWidthDp > config.screenHeightDp
        val panelWidth = if (sidePanel) kotlin.math.min(310, config.screenWidthDp / 2 - 12) else 0
        val root = FrameLayout(this).apply { setBackgroundColor(navy) }
        window.statusBarColor = navy
        window.navigationBarColor = navy
        WindowCompat.getInsetsController(window, root).apply {
            isAppearanceLightStatusBars = false
            isAppearanceLightNavigationBars = false
        }
        val headerCard = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(11), dp(6), dp(3), dp(6))
            background = dashboardSurface(Color.argb(244, 13, 25, 38), 18, Color.rgb(48, 64, 78))
            elevation = dp(3).toFloat()
        }
        headerCard.addView(android.view.View(this).apply {
            background = dashboardSurface(lime, 3, lime)
        }, LinearLayout.LayoutParams(dp(4), dp(40)).apply { marginEnd = dp(10) })
        val headerColumn = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        headerText = TextView(this).apply {
            text = getString(R.string.header_title)
            textSize = 22f
            typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
            setTextColor(Color.WHITE)
            maxLines = 1
            ellipsize = android.text.TextUtils.TruncateAt.END
            isClickable = true
            isFocusable = true
            contentDescription = getString(R.string.nickname_accessibility)
            setOnClickListener { showNicknameDialog(required = false) }
        }
        headerColumn.addView(headerText)
        headerColumn.addView(TextView(this).apply {
            text = getString(R.string.brand_tagline)
            textSize = 11f
            setTextColor(Color.rgb(204, 221, 227))
            maxLines = 2
        })
        headerCard.addView(headerColumn, LinearLayout.LayoutParams(0, -2, 1f))
        val options = Button(this).apply {
            text = "⋮"
            contentDescription = getString(R.string.dashboard_menu)
            styleActionButton(this, primary = false, quiet = true)
            textSize = 25f
            setPadding(0, 0, 0, 0)
            setOnClickListener { anchor -> showDashboardMenu(anchor) }
        }
        headerCard.addView(options, LinearLayout.LayoutParams(dp(48), dp(48)))
""")

# Map source, overlay and navigation remain exactly as before. Reparent only controls.
block("        mapFrame.addView(locate, FrameLayout.LayoutParams", "        val compassReset = Button(this).apply {", "")
# North reset still follows the original click/touch behavior and appears after map rotation.
for old, new in [
    ("minWidth = dp(42)", "minWidth = dp(48)"),
    ("minimumWidth = dp(42)", "minimumWidth = dp(48)"),
    ("minHeight = dp(42)", "minHeight = dp(48)"),
    ("minimumHeight = dp(42)", "minimumHeight = dp(48)"),
]:
    once(old, new)
block("        mapFrame.addView(compassReset, FrameLayout.LayoutParams", "        // Keep the map uncluttered:", "")
once("        root.addView(mapFrame, LinearLayout.LayoutParams(-1, 0, 1f))", """        root.addView(mapFrame, FrameLayout.LayoutParams(-1, -1).apply {
            if (sidePanel) marginEnd = dp(panelWidth + 16)
        })""")
block("        mapFrame.addView(attribution, FrameLayout.LayoutParams", "        val badgeList = BadgeManager.badges(this, store)", """        val topOverlay = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        topOverlay.addView(headerCard, LinearLayout.LayoutParams(-1, -2))
        val toolRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.TOP
        }
        val attributionHolder = FrameLayout(this)
        attributionHolder.addView(attribution, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.START))
        toolRow.addView(attributionHolder, LinearLayout.LayoutParams(0, -2, 1f).apply { marginEnd = dp(5) })
        val mapControls = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.END
        }
        mapControls.addView(locate, LinearLayout.LayoutParams(-2, dp(48)))
        mapControls.addView(compassReset, LinearLayout.LayoutParams(dp(48), dp(48)).apply { topMargin = dp(8) })
        toolRow.addView(mapControls, LinearLayout.LayoutParams(-2, -2))
        topOverlay.addView(toolRow, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(8) })
        mapFrame.addView(topOverlay, FrameLayout.LayoutParams(-1, -2, Gravity.TOP or Gravity.START).apply {
            setMargins(dp(12), dp(10), dp(12), 0)
        })

        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(14), dp(12), dp(14), dp(14))
            background = dashboardSurface(Color.argb(248, 15, 29, 43), 24, Color.rgb(61, 80, 94))
        }
        val titleRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        titleRow.addView(TextView(this).apply {
            text = getString(R.string.dashboard_footsteps)
            textSize = 16f
            typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
            setTextColor(Color.WHITE)
        }, LinearLayout.LayoutParams(0, -2, 1f))
        trackingStatusText = TextView(this).apply {
            textSize = 12f
            setTextColor(lime)
            typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
            gravity = Gravity.END
        }
        titleRow.addView(trackingStatusText, LinearLayout.LayoutParams(-2, -2))
        panel.addView(titleRow)
        countText = TextView(this).apply {
            text = "—"
            textSize = 34f
            setTextColor(Color.WHITE)
            typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
            maxLines = 1
            includeFontPadding = false
            setAutoSizeTextTypeUniformWithConfiguration(18, 34, 1, android.util.TypedValue.COMPLEX_UNIT_SP)
            gravity = Gravity.CENTER_VERTICAL
        }
        percentText = TextView(this).apply {
            text = getString(R.string.dashboard_earth_percent, "—")
            textSize = 11f
            setTextColor(Color.rgb(208, 222, 231))
            setPadding(0, dp(3), 0, dp(2))
        }
""")
block("        if (countText.parent === panel) panel.removeView(countText)", "        val accountBackupButton = Button(this).apply {", """        val summaryRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val metricsColumn = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        metricsColumn.addView(countText, LinearLayout.LayoutParams(-1, dp(46)))
        metricsColumn.addView(percentText, LinearLayout.LayoutParams(-1, -2))
        summaryRow.addView(metricsColumn, LinearLayout.LayoutParams(0, -2, 1f))
        // Preserve the existing badge and combined cloud/account actions.
        val accountToolsColumn = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
        }
        accountToolsColumn.addView(badgesButton, LinearLayout.LayoutParams(-1, dp(48)))
""")
block("        accountToolsColumn.addView(accountBackupButton, LinearLayout.LayoutParams", "        // MY_EARTH_CLOUD_BACKUP_BUTTON:", """        accountToolsColumn.addView(accountBackupButton, LinearLayout.LayoutParams(-1, dp(48)).apply {
            topMargin = dp(4)
        })
        val accountWidth = if (config.screenWidthDp < 350 || sidePanel) 104 else 120
        summaryRow.addView(accountToolsColumn, LinearLayout.LayoutParams(dp(accountWidth), -2).apply {
            marginStart = dp(8)
        })
        panel.addView(summaryRow, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(6) })
        recordActionButton = Button(this).apply {
            text = getString(R.string.explore_start)
            styleActionButton(this, primary = true)
            setOnClickListener {
                if (LocationTrackingService.isRunning) {
                    startRequestedAt = 0L
                    stopService(Intent(this@MainActivity, LocationTrackingService::class.java))
                    refreshTrackingStatus()
                    refreshFog()
                } else if (startRequestedAt == 0L) {
                    requestAndStart()
                }
            }
        }
        panel.addView(recordActionButton, LinearLayout.LayoutParams(-1, dp(52)).apply { topMargin = dp(12) })

""")
once("        root.addView(panel); setContentView(root)", """        root.addView(panel, FrameLayout.LayoutParams(
            if (sidePanel) dp(panelWidth) else -1,
            -2,
            Gravity.BOTTOM or Gravity.END
        ).apply {
            setMargins(dp(12), 0, dp(12), dp(12))
        })
        setContentView(root)""")

block("    private fun styleActionButton(", "    private fun confirmCloudBackupOptIn()", """    private fun dashboardSurface(fill: Int, radius: Int, stroke: Int) =
        android.graphics.drawable.GradientDrawable().apply {
            setColor(fill)
            cornerRadius = dp(radius).toFloat()
            setStroke(dp(1), stroke)
        }

    private fun showDashboardMenu(anchor: android.view.View) {
        android.widget.PopupMenu(this, anchor).apply {
            menu.add(0, 1, 0, R.string.nickname_change_title)
            menu.add(0, 2, 1, R.string.location_permission_settings)
            menu.add(0, 3, 2, R.string.privacy_policy)
            setOnMenuItemClickListener { item ->
                when (item.itemId) {
                    1 -> { showNicknameDialog(required = false); true }
                    2 -> { openAppSettings(); true }
                    3 -> { startActivity(Intent(this@MainActivity, PrivacyPolicyActivity::class.java)); true }
                    else -> false
                }
            }
            show()
        }
    }

    private fun styleActionButton(
        button: Button,
        primary: Boolean,
        floating: Boolean = false,
        compact: Boolean = false,
        quiet: Boolean = false
    ) {
        val fill = when {
            floating -> Color.rgb(246, 251, 255)
            primary -> Color.rgb(177, 235, 111)
            quiet -> Color.TRANSPARENT
            else -> Color.rgb(37, 54, 69)
        }
        val ink = if (floating || primary) Color.rgb(12, 27, 30) else Color.rgb(232, 241, 246)
        val stroke = if (quiet) Color.TRANSPARENT else if (primary || floating) fill else Color.rgb(69, 90, 105)
        val shape = dashboardSurface(fill, if (primary || floating) 26 else 16, stroke)
        button.apply {
            isAllCaps = false
            textSize = if (compact) 12f else if (primary) 16f else 13f
            setTextColor(ink)
            typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
            minHeight = dp(48)
            minimumHeight = dp(48)
            minWidth = 0
            minimumWidth = 0
            setPadding(dp(if (compact) 5 else 11), 0, dp(if (compact) 5 else 11), 0)
            backgroundTintList = null
            background = android.graphics.drawable.RippleDrawable(
                android.content.res.ColorStateList.valueOf(if (primary || floating) Color.argb(40, 0, 0, 0) else Color.argb(45, 255, 255, 255)),
                shape,
                null
            )
            elevation = dp(if (floating) 3 else 0).toFloat()
            stateListAnimator = null
        }
    }

""")
once("""            trackingStatusText.text = "● 탐험 시작 요청됨 · GPS 연결 확인 중"
            refreshTrackingStatus()
        } catch (e: Exception) {
            countText.text = "탐험을 시작하지 못했습니다. 위치 권한과 기기 설정을 확인하세요."
""", """            startRequestedAt = android.os.SystemClock.elapsedRealtime()
            refreshTrackingStatus()
        } catch (e: Exception) {
            startRequestedAt = 0L
            refreshTrackingStatus()
            Toast.makeText(this, R.string.tracking_failed, Toast.LENGTH_LONG).show()
""")
once("                        countText.text = getString(R.string.exploration_summary, percentLabel, areaLabel)", """                        countText.text = areaLabel
                        countText.contentDescription = getString(R.string.dashboard_area_accessibility, areaLabel)
                        percentText.text = getString(R.string.dashboard_earth_percent, percentLabel)""")
once("                            countText.text = getString(R.string.map_load_failed)", """                            percentText.text = getString(R.string.map_load_failed)""")
block("    private fun refreshTrackingStatus() {", "    private fun restoreMapViewportIfAvailable", """    private fun refreshTrackingStatus() {
        if (!::trackingStatusText.isInitialized || !::recordActionButton.isInitialized) return
        val running = LocationTrackingService.isRunning
        val now = android.os.SystemClock.elapsedRealtime()
        if (running || (startRequestedAt != 0L && now - startRequestedAt >= 7_000L)) {
            startRequestedAt = 0L
        }
        val pending = startRequestedAt != 0L
        val label = getString(when {
            running -> R.string.dashboard_recording
            pending -> R.string.dashboard_starting
            else -> R.string.dashboard_stopped
        })
        if (trackingStatusText.text.toString() != label) {
            trackingStatusText.text = label
            trackingStatusText.setTextColor(if (running) Color.rgb(177, 235, 111) else Color.rgb(193, 212, 222))
            trackingStatusText.contentDescription = getString(when {
                running -> R.string.tracking_active
                pending -> R.string.tracking_requested
                else -> R.string.tracking_inactive
            })
        }
        val action = getString(when {
            running -> R.string.explore_stop
            pending -> R.string.dashboard_starting
            else -> R.string.explore_start
        })
        if (recordActionButton.text.toString() != action) recordActionButton.text = action
        recordActionButton.isEnabled = !pending
        recordActionButton.alpha = if (pending) 0.7f else 1f
    }

""")
once("""        refreshTrackingStatus()
        refreshFog()
    }
    override fun onStop() { if (receiverRegistered) { unregisterReceiver(trackingReceiver); receiverRegistered = false }; super.onStop() }""", """        dashboardHandler.removeCallbacks(dashboardStatusPoll)
        dashboardStatusPoll.run()
        refreshFog()
    }
    override fun onStop() {
        dashboardHandler.removeCallbacks(dashboardStatusPoll)
        if (receiverRegistered) { unregisterReceiver(trackingReceiver); receiverRegistered = false }
        super.onStop()
    }""")
once("    override fun onDestroy() {\n        zoomAnimator?.cancel()", """    override fun onDestroy() {
        dashboardHandler.removeCallbacks(dashboardStatusPoll)
        zoomAnimator?.cancel()""")

# Preserve security-sensitive account dialog, Google authentication and core map calculations.
def section(text, start, end):
    a = text.index(start)
    return text[a:text.index(end, a)]

for start, end in [
    ("        val accountBackupButton = Button(this).apply {", "        accountToolsColumn.addView(accountBackupButton,"),
    ("    private fun confirmCloudBackupOptIn()", "    private fun startLocationTrackingService()"),
    ("    override fun onActivityResult(", "    private fun confirmAccountDeletion()"),
    ("                        val earthSurfaceAreaM2 =", "                        val percentLabel ="),
    ("    private fun goToCurrentLocation()", "    override fun onStart()"),
]:
    assert section(original, start, end) == section(s, start, end), f"Protected section changed: {start}"

main.write_text(s, encoding="utf-8")
for folder, values in {
    "values": {
        "dashboard_menu": "App menu",
        "dashboard_footsteps": "👣 My footsteps",
        "dashboard_earth_percent": "Earth map share: %1$s",
        "dashboard_area_accessibility": "Recorded area: %1$s",
        "dashboard_recording": "● Recording",
        "dashboard_starting": "● Starting…",
        "dashboard_stopped": "● Stopped",
    },
    "values-ko": {
        "dashboard_menu": "앱 메뉴",
        "dashboard_footsteps": "👣 나의 발자취",
        "dashboard_earth_percent": "지구 전체 지도 대비 %1$s",
        "dashboard_area_accessibility": "기록된 영역 %1$s",
        "dashboard_recording": "● 기록 중",
        "dashboard_starting": "● 시작 중…",
        "dashboard_stopped": "● 기록 중지",
    },
}.items():
    path = root / f"app/src/main/res/{folder}/strings.xml"
    xml = path.read_text(encoding="utf-8")
    assert xml.count("</resources>") == 1
    assert all(f'name="{name}"' not in xml for name in values)
    extra = "".join(f'    <string name="{name}">{value}</string>\n' for name, value in values.items())
    xml = xml.replace("</resources>", extra + "</resources>")
    ET.fromstring(xml)
    path.write_text(xml, encoding="utf-8")

for path in [root / "app/build.gradle.kts", root / "scripts/verify-play-release-policy.py"]:
    txt = path.read_text(encoding="utf-8")
    assert txt.count("versionCode = 98") == 1
    assert txt.count('versionName = "0.10.45"') == 1
    path.write_text(txt.replace("versionCode = 98", "versionCode = 99").replace('versionName = "0.10.45"', 'versionName = "0.10.46"'), encoding="utf-8")

print("Applied v0.10.46 A dashboard; protected auth and map sections unchanged.")
