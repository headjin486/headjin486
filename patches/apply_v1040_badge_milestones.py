from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
badge_file = pkg / "BadgeManager.kt"
s = badge_file.read_text(encoding="utf-8")

old_distance = '''            ExplorerBadge("km1", "산책가", "누적 1km 탐험", "🥾", km >= 1),
            ExplorerBadge("km10", "탐험가", "누적 10km 탐험", "🧭", km >= 10),
            ExplorerBadge("km50", "모험가", "누적 50km 탐험", "🏕️", km >= 50),
            ExplorerBadge("km100", "지구 여행자", "누적 100km 탐험", "🌍", km >= 100),
            ExplorerBadge("km500", "대탐험가", "누적 500km 탐험", "🚩", km >= 500),'''
new_distance = '''            ExplorerBadge("km100", "장거리 탐험가", "누적 이동 거리 100km 달성", "🥾", km >= 100),
            ExplorerBadge("km1000", "대륙 횡단자", "누적 이동 거리 1,000km 달성", "🧭", km >= 1000),
            ExplorerBadge("km10000", "세계 일주 탐험가", "누적 이동 거리 10,000km 달성", "🏕️", km >= 10000),
            ExplorerBadge("km100000", "지구의 발자취", "누적 이동 거리 100,000km 달성", "🌍", km >= 100000),'''
if old_distance not in s:
    raise SystemExit("Existing distance badge thresholds not found; refusing unsafe patch")
s = s.replace(old_distance, new_distance, 1)

old_area = '''            ExplorerBadge("area1", "안개 걷기", "누적 해금 면적 1km²", "🌤️", area >= 1),
            ExplorerBadge("area10", "새로운 세상", "누적 해금 면적 10km²", "🗺️", area >= 10),
            ExplorerBadge("area50", "영역 개척자", "누적 해금 면적 50km²", "🏅", area >= 50),'''
new_area = '''            ExplorerBadge("area10", "안개 개척자", "누적 해금 면적 10km²", "🌤️", area >= 10),
            ExplorerBadge("area100", "새로운 세상", "누적 해금 면적 100km²", "🗺️", area >= 100),
            ExplorerBadge("area1000", "대지의 개척자", "누적 해금 면적 1,000km²", "🏅", area >= 1000),
            ExplorerBadge("area10000", "광대한 세계", "누적 해금 면적 10,000km²", "🌏", area >= 10000),'''
if old_area not in s:
    raise SystemExit("Existing explored-area badge thresholds not found; refusing unsafe patch")
s = s.replace(old_area, new_area, 1)
badge_file.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 92' not in g or 'versionName = "0.10.39"' not in g:
    raise SystemExit("Unexpected base app version; refusing unsafe version bump")
g = g.replace('versionCode = 92', 'versionCode = 93', 1)
g = g.replace('versionName = "0.10.39"', 'versionName = "0.10.40"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 92' not in v or 'versionName = "0.10.39"' not in v:
    raise SystemExit("Unexpected release verifier base version")
v = v.replace('versionCode = 92', 'versionCode = 93', 1)
v = v.replace('versionName = "0.10.39"', 'versionName = "0.10.40"', 1)
verifier.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.40: raise cumulative distance and explored-area badge milestones.")
