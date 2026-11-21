from pathlib import Path
import subprocess, sys

root = Path(sys.argv[1])
res = root / "app/src/main/res"
svg = r"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#08794B"/><stop offset=".52" stop-color="#00563A"/><stop offset="1" stop-color="#002D27"/></linearGradient>
 <radialGradient id="glow"><stop stop-color="#23D879" stop-opacity=".45"/><stop offset="1" stop-color="#00A85B" stop-opacity="0"/></radialGradient>
 <linearGradient id="earth" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#5CF3D2"/><stop offset=".45" stop-color="#13A88B"/><stop offset="1" stop-color="#00634D"/></linearGradient>
 <linearGradient id="trail" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#FFFFFF"/><stop offset=".55" stop-color="#E6FFD0"/><stop offset="1" stop-color="#9BFF70"/></linearGradient>
 <filter id="soft"><feGaussianBlur stdDeviation="24"/></filter>
 <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="12"/></filter>
 <clipPath id="round"><rect x="20" y="20" width="984" height="984" rx="210"/></clipPath>
</defs>
<g clip-path="url(#round)">
 <rect width="1024" height="1024" fill="url(#bg)"/>
 <ellipse cx="510" cy="490" rx="480" ry="420" fill="url(#glow)"/>
 <g fill="#D9FFF1">
  <circle cx="140" cy="180" r="5"/><circle cx="250" cy="270" r="4"/><circle cx="810" cy="160" r="6"/><circle cx="890" cy="310" r="4"/><circle cx="720" cy="245" r="4"/><circle cx="165" cy="390" r="5"/>
 </g>
 <path d="M-40 770 Q190 525 420 515 Q690 500 1060 700 L1060 1080 L-40 1080Z" fill="#00E5C2" opacity=".22" filter="url(#soft)"/>
 <path d="M-55 790 Q175 545 420 530 Q695 510 1080 700 L1080 1080 L-55 1080Z" fill="url(#earth)"/>
 <path d="M-20 820 Q180 605 405 590 Q690 575 1040 740" fill="none" stroke="#8CFFE6" stroke-width="10" opacity=".72"/>
 <path d="M110 715 Q260 650 360 640 Q450 630 500 585 Q550 535 665 535 Q790 535 900 610" fill="none" stroke="#004D40" stroke-width="5" opacity=".35"/>
 <path d="M160 785 Q260 720 390 708 Q505 696 545 655 Q600 595 750 610 Q830 620 930 690" fill="none" stroke="#B7FFE9" stroke-width="4" opacity=".45"/>
 <g fill="#8CF5C8" opacity=".65">
  <path d="M125 785l38-40 48 8 18 30-33 23-49-3z"/><path d="M340 670l45-25 42 10 12 30-31 18-52-6z"/><path d="M590 725l36-35 55 5 24 32-39 27-62-5z"/><path d="M800 785l38-30 42 12 9 26-44 18z"/>
 </g>
 <!-- A continuous personal footprint route -->
 <path d="M120 430 C260 345 390 390 490 440 C590 490 735 475 845 400 C920 350 970 355 1040 390" fill="none" stroke="#8DFF5D" stroke-width="54" stroke-linecap="round" opacity=".28" filter="url(#soft)"/>
 <path d="M105 425 C250 345 385 385 485 435 C590 488 735 475 845 400 C920 350 970 355 1040 390" fill="none" stroke="url(#trail)" stroke-width="38" stroke-linecap="round"/>
 <path d="M105 425 C250 345 385 385 485 435 C590 488 735 475 845 400 C920 350 970 355 1040 390" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" opacity=".9"/>
 <!-- Hiker silhouette with backpack -->
 <ellipse cx="512" cy="550" rx="110" ry="32" fill="#001E18" opacity=".35" filter="url(#shadow)"/>
 <circle cx="512" cy="172" r="43" fill="#FFFFFF" stroke="#004A35" stroke-width="12"/>
 <path d="M466 230 Q512 210 558 230 L579 340 Q584 383 558 400 L466 400 Q440 383 445 340Z" fill="#FFFFFF" stroke="#004A35" stroke-width="14" stroke-linejoin="round"/>
 <path d="M462 250 Q425 260 414 315 L392 382 Q383 410 407 422 Q430 433 442 408 L470 330" fill="#FFFFFF" stroke="#004A35" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>
 <path d="M562 250 Q599 260 610 315 L632 382 Q641 410 617 422 Q594 433 582 408 L554 330" fill="#FFFFFF" stroke="#004A35" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>
 <path d="M470 395 L468 525 Q466 555 494 558 Q520 560 522 530 L526 430 L530 530 Q532 560 558 558 Q586 555 584 525 L578 395" fill="#FFFFFF" stroke="#004A35" stroke-width="15" stroke-linejoin="round"/>
 <path d="M468 260 Q512 286 556 260 L564 324 Q512 352 460 324Z" fill="#E9FFF4" stroke="#004A35" stroke-width="10" stroke-linejoin="round"/>
 <path d="M493 225 L531 225" stroke="#004A35" stroke-width="10" stroke-linecap="round"/>
 <!-- Title -->
 <text x="512" y="748" text-anchor="middle" font-family="DejaVu Sans, Noto Sans CJK KR, sans-serif" font-size="112" font-weight="800" letter-spacing="-5" fill="#FFFFFF">MY <tspan fill="#B8FF65">EARTH</tspan></text>
 <path d="M215 805 H340 M684 805 H809" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" opacity=".9"/>
 <text x="512" y="842" text-anchor="middle" font-family="Noto Sans CJK KR, NanumGothic, sans-serif" font-size="68" font-weight="700" fill="#FFFFFF">마이 어스</text>
</g>
</svg>"""
svg_path = root / "my_earth_icon_v106.svg"
svg_path.write_text(svg, encoding="utf-8")
png_path = root / "my_earth_icon_v106.png"
subprocess.run([sys.executable, "-m", "cairosvg", str(svg_path), "-o", str(png_path), "-s", "1"], check=True)

# Adaptive icon on Android 8+ and high-resolution legacy icon for older launchers.
drawable = res / "drawable-nodpi"
drawable.mkdir(parents=True, exist_ok=True)
import shutil
shutil.copyfile(png_path, drawable / "my_earth_icon_v106.png")
adaptive = res / "mipmap-anydpi-v26/ic_launcher.xml"
adaptive.parent.mkdir(parents=True, exist_ok=True)
adaptive.write_text('''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/launcher_background" />
    <foreground android:drawable="@drawable/my_earth_icon_v106" />
</adaptive-icon>
''', encoding="utf-8")
legacy = res / "mipmap-nodpi"
legacy.mkdir(parents=True, exist_ok=True)
shutil.copyfile(png_path, legacy / "ic_launcher.png")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 59' not in g or 'versionName = "0.10.5"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 59', 'versionCode = 60', 1)
g = g.replace('versionName = "0.10.5"', 'versionName = "0.10.6"', 1)
gradle.write_text(g, encoding="utf-8")

assert png_path.stat().st_size > 10000
assert "@drawable/my_earth_icon_v106" in adaptive.read_text(encoding="utf-8")
assert (legacy / "ic_launcher.png").exists()
print("v0.10.6 verified: crisp 1024px vector-rendered MY EARTH / 마이 어스 launcher icon applied")
