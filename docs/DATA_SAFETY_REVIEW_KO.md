# MY EARTH Data Safety 사전 점검표 (내부 초안)

작성일: 2026-11-22  
대상 빌드: v0.10.28 / versionCode 81  
AAB SHA-256: f64326c87f920ef7b035d5e3da634ee1e01e4e95514ea70f9cb91ac2074d6b5e

> 이 문서는 Play Console 설문을 대신하는 최종 답변이 아니다. 실제 Firebase Auth 프로필 필드, 네트워크 트래픽, 지도 타일 제공자 및 계정 삭제 운영을 확인한 후 확정한다.

## 1. AAB에서 확인한 항목 (v0.10.28)

- AAB 패키지명: com.earthunlock.app
- AAB 버전: 0.10.28 / versionCode 81
- 빌드 산출물: app-release.aab
- AAB JAR 서명 검증: jarsigner에서 서명 검증 성공. 업로드 키 인증서는 자체 서명이며 공개 CA 체인으로 검증되는 인증서가 아님.
- 의존성 메타데이터에서 확인: Firebase Authentication, Firebase Firestore, osmdroid, Google Play services Location
- 의존성 메타데이터에서 AdMob 및 Firebase Analytics SDK는 확인되지 않음. 이는 광고·분석 SDK가 없다는 강한 단서이나, 최종적으로 모든 모듈 및 네트워크 트래픽을 대조해야 함.
- 소스 프로젝트의 Gradle 설정: compileSdk 36 / targetSdk 36 / minSdk 26
- AAB의 manifest permission 문자열에서 확인: INTERNET, ACCESS_COARSE_LOCATION, ACCESS_FINE_LOCATION, FOREGROUND_SERVICE, FOREGROUND_SERVICE_LOCATION
- ACCESS_BACKGROUND_LOCATION은 v0.10.28 AAB manifest의 권한 문자열에서 확인되지 않음.
- OSM 타일 엔드포인트: `https://tile.openstreetmap.org/`
- DEX의 User-Agent: `MY EARTH/0.10.28 (Android; com.earthunlock.app; contact: headjin486@gmail.com)` 확인. 이전 `EarthExplorer/0.7.6` 문자열은 발견되지 않음.
- LocationTrackingService는 location foreground service로 선언되어 있음.

## 2. Data Safety 분류 후보

| Play Console 데이터 유형 | 현재 파악 | 후보 목적 / 처리 |
|---|---|---|
| 위치 - 정확한 위치 | 클라우드 백업 시 5m 격자 셀 좌표가 Firebase Firestore로 전송됨. 원본 GPS 좌표·시간순 경로는 로컬 저장 | 앱 기능 / 선택형 지도 백업 |
| 개인 정보 - 이메일 주소 | Google 계정 연결 시 Firebase Authentication이 이메일을 처리할 가능성이 높음. 실제 Firebase 사용자 레코드 확인 필요 | 계정 관리 |
| 기기 또는 기타 ID - 사용자 ID | Firebase UID로 백업 문서와 계정을 연결 | 계정 관리 / 백업 복원 |
| 개인 정보 - 이름(닉네임) | 앱 닉네임은 로컬 프로필에 저장되는 것으로 파악. 클라우드 전송 여부 확인 필요 | 로컬 표시 목적이라면 수집 아님 |

주의:
- 원본 GPS 경로가 서버로 전송되지 않더라도 5m 셀 ID는 실제 위치를 매우 좁은 영역으로 특정할 수 있으므로 위치 데이터 수집으로 분류하는 방향이 안전하다.
- 로컬에서만 처리되고 기기 밖으로 전송되지 않는 GPS 기록은 Google Data Safety의 '수집'과 구분한다.
- Google Play는 SDK가 전송하는 데이터도 앱의 데이터 처리로 포함한다.
- Firebase를 서비스 제공자로 사용하는 경우에도 해당 데이터 유형과 목적을 숨기지 않는다. 공유 여부는 Google의 service provider 예외 및 Firebase 계약/처리 관계를 대조한다.

## 3. 설문 답변을 확정하기 전 반드시 확인할 것

1. Firebase Authentication 사용자 레코드에서 Google 연결 계정의 email, displayName, providerData 중 실제 저장되는 필드를 확인한다.
2. Firebase UID가 사용자 계정과 연결되는 식별자이므로 사용자 ID 항목으로 신고한다.
3. 클라우드 백업이 선택 동의 후에만 시작되는지, 거부 상태에서 Firestore 쓰기가 발생하지 않는지 확인한다.
4. Firestore의 백업 문서와 updatedAt 이외에 추가 필드가 없는지 확인한다.
5. 앱의 모든 네트워크 요청에서 OSM 타일 제공자와 Firebase 외 다른 수신자가 있는지 확인한다.
6. 광고 SDK/Analytics SDK가 없다는 의존성 확인을 최종 AAB 전체 모듈과 실제 네트워크 관찰로 재확인한다.
7. 데이터 암호화 전송, 계정 삭제, 백업 삭제, 보유기간을 실제 동작과 맞춘다.

## 4. 지도 타일 제공자 주의사항

현재 앱은 osmdroid를 사용하고 있으며, 공개 안내문은 OpenStreetMap 기반 타일을 언급한다. 그러나 실제 빌드의 타일 URL과 User-Agent 설정을 확인해야 한다.

OpenStreetMap 표준 타일 서버(tile.openstreetmap.org)를 사용하는 경우:
- 타일 요청은 서버/CDN에 도달하며 IP 주소와 요청 타일 정보 등 네트워크 운영 데이터가 처리될 수 있다.
- OSMF 개인정보처리방침과 타일 사용 정책을 개인정보처리방침에 반영한다.
- 타일 사용 정책은 서비스 용량, 식별 가능한 User-Agent, 캐시 및 사전 다운로드 금지 조건을 둔다.
- OSMF는 자체 표준 타일 서버를 상업용 타일 서비스로 보장하지 않으며, 상업 서비스의 접근을 중단할 수 있다고 명시한다.
- MY EARTH가 향후 광고 등 수익화할 경우, 공개 OSM 표준 타일을 계속 사용하는 것이 적절한지 재검토하고 상업 이용 조건이 명확한 타일 제공자로 전환하는 것이 바람직하다.

참고:
- https://operations.osmfoundation.org/policies/tiles/
- https://osmfoundation.org/wiki/Privacy_Policy

## 5. 계정 삭제 상태

- 앱 내부 계정 삭제 기능은 v0.10.27에 포함되었고 사용자 테스트를 완료했다.
- 앱 내부 삭제는 Firebase Auth 계정과 UID에 연결된 Firestore 백업 청크를 삭제한다.
- 로컬 GPS 기록 및 지도 데이터는 별도 보존된다.
- 외부 삭제 경로는 이메일 접수 방식이며 자동 삭제가 아니다.
- 이메일 요청의 소유자 확인, 처리 담당자, 처리 기한, 삭제 확인 및 회신을 운영자가 실제로 수행할 절차를 정하고 테스트해야 한다.

## 6. 최종 확정 체크리스트

- [ ] Firebase Auth 사용자 레코드의 실제 필드 확인
- [ ] 클라우드 백업 거부/동의 시 Firestore 트래픽 비교
- [ ] 타일 URL 및 User-Agent 실제 값 확인
- [ ] OSM 요청에 전달되는 네트워크 데이터 확인
- [ ] 모든 AAB SDK 및 외부 수신자 검증
- [ ] Data Safety의 수집/공유/선택 여부/목적 확정
- [ ] 계정 삭제 이메일 처리 운영자·기한·절차 확정 및 테스트
- [ ] 개인정보처리방침의 타일 제공자, Firebase, 보유·삭제 설명 업데이트


## 7. v0.10.28 기준 재확인 메모

- 이 문서는 v0.10.28 AAB를 기준으로 갱신했지만 Data Safety 최종 설문을 확정한 것은 아니다.
- AAB 정적 분석만으로는 실제 네트워크 전송 여부, Firebase Auth 프로필 필드, Firestore 백업 거부 상태의 쓰기 여부를 확정할 수 없다.
- 실기기에서 선택형 백업 동의/거부, Google 계정 연결, 계정 삭제를 재시험한 뒤 체크리스트를 완료한다.
- 광고 및 분석 SDK는 AAB 의존성 메타데이터에서 확인되지 않았으나, 전체 SDK 및 실제 트래픽 대조 전까지 최종 신고 문구로 단정하지 않는다.
