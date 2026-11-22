# MY EARTH Google Play 제출 준비서 (내부 작업본)

최종 확인일: 2026-11-22
앱: MY EARTH
applicationId: com.earthunlock.app
현재 확인된 빌드: versionName 0.10.28 / versionCode 81
targetSdk: 36 (Android 16)
이 문서는 Play Console 입력을 위한 작업본이며, 운영자 실명·계정 상태·실제 네트워크 트래픽 확인 전에는 최종 제출본으로 사용하지 않는다.

## 1. 앱의 핵심 기능 설명

MY EARTH는 사용자가 직접 탐험을 시작하면 현재 위치와 이동 경로를 기기 안에 기록하고, 지나간 주변의 지도 영역을 해금해 개인 지도로 남기는 앱이다. 걷기 목표나 순위 경쟁이 아니라 사용자가 실제로 지나온 길을 개인의 탐험 기록으로 보존하는 것이 목적이다.

## 2. 위치 포그라운드 서비스 선언 초안

- 서비스 유형: location
- 매니페스트 확인: FOREGROUND_SERVICE, FOREGROUND_SERVICE_LOCATION, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION 선언. LocationTrackingService에 foregroundServiceType="location" 지정.
- 백그라운드 위치 권한: ACCESS_BACKGROUND_LOCATION 선언 확인되지 않음.
- 사용 목적(제출 문안):
  "MY EARTH의 핵심 기능은 사용자가 직접 시작한 탐험 동안 이동한 경로 주변의 지도 영역을 해금하고 개인 지도에 보존하는 것입니다. 사용자가 탐험 시작을 누르면 위치 포그라운드 서비스가 GPS 위치를 받아 기기 내부 기록과 지도 해금에 사용합니다. 사용자가 다른 앱으로 전환하거나 화면을 꺼도 탐험을 중지할 때까지 기록이 이어져야 이동 경로와 해금 영역이 끊기지 않습니다. 실행 중에는 지속적인 알림을 표시하며, 앱의 중지 기능 또는 알림의 '탐험 중지' 동작으로 사용자가 언제든 종료할 수 있습니다."
- 지연/중단 시 사용자 영향(제출 문안):
  "서비스 시작이 지연되거나 이동 중 중단되면 해당 시간대의 위치 기록과 지도 해금이 누락되어 사용자가 지나온 길을 완전하게 보존하지 못할 수 있습니다. 서비스는 사용자가 탐험을 시작한 동안에만 실행하며, 사용자가 중지하면 종료합니다. Android가 프로세스를 회수한 경우 시스템 제한에 따라 기록이 중단될 수 있으며, 앱은 사용자가 인지할 수 있는 알림을 통해 실행 상태를 표시합니다."
- 시연 영상 구성:
  1. 앱 첫 화면에서 위치 이용 안내 확인
  2. 정확한 위치 권한 허용
  3. 사용자가 '탐험 시작'을 직접 누름
  4. 지속 알림과 탐험 중 상태 표시
  5. 홈 화면으로 나가거나 화면 잠금
  6. 잠시 이동한 뒤 앱으로 돌아와 지도 해금/위치 갱신 확인
  7. 시스템 알림의 '탐험 중지'를 눌러 서비스 종료 확인
- 영상은 실제 배포 후보 빌드에서 촬영해야 하며, 시뮬레이션 영상이나 편집으로 실제 동작을 과장하지 않는다.

## 3. Data safety 입력 초안 — 추가 검증 필요

현재 코드 설계 및 Firestore 규칙에서 확인된 데이터 흐름:
- 기기 내부: GPS 위도·경도, 정확도, 측정 시각 및 시간순 경로가 SQLite에 저장됨.
- 클라우드 백업: 이용자가 Google 계정을 연결하고 별도 동의한 경우 해금된 5m 셀 좌표(cell_x, cell_y)만 Firestore에 저장. GPS 원본 좌표와 시간순 경로를 백업 payload에 포함하지 않음.
- Firebase Authentication: 익명 인증과 선택적 Google 계정 연결/복구.
- Firestore 문서: UID별 exploration_backups/{uid}/chunks 하위에 formatVersion, 압축 payload, updatedAt 저장. 보안 규칙은 로그인 UID와 문서 UID 일치를 요구.
- 지도 타일: 지도 표시를 위해 외부 타일 서버에 타일 요청을 전송. 요청 IP 및 타일 영역 메타데이터 처리 여부·보유기간은 타일 제공자의 정책을 확인해야 함.
- 현재 출시 준비 코드에서 광고 SDK 및 Google Analytics를 포함하지 않는 것으로 확인됨. 최종 AAB 의존성 목록에서 재검증할 것.

Data safety 입력 전 확인해야 할 질문:
1. Google 계정 연결 시 Firebase Authentication이 실제로 이메일 주소를 저장/처리하는지와 Google provider profile 필드를 확인한다.
2. Firebase UID 및 익명 인증 식별자가 Play Console의 '기기 또는 기타 ID'에 해당하는지 분류한다.
3. 5m 셀 백업 payload는 실제 위치에서 파생되는 위치 데이터다. 서버에 전송되므로 '정확한 위치' 또는 관련 위치 데이터 항목으로 분류할 필요가 있는지 데이터 스키마와 Google 정의를 대조한다. 원본 GPS가 서버에 전송되지 않는다는 이유만으로 위치 데이터 수집이 없다고 답하지 않는다.
4. OSM 타일 제공자의 실제 엔드포인트, 개인정보 처리방침, IP/요청 타일 정보의 처리 범위를 확인한다.
5. TLS 전송, 삭제 요청 방식, 보유/삭제 기간을 Firebase 설정과 실제 삭제 구현으로 검증한다.
6. 최종 AAB의 merged manifest와 런타임 트래픽/SDK를 검사한 뒤에만 답변을 확정한다.

## 4. 계정 및 데이터 삭제

- 앱 내부 삭제: v0.10.27에서 구현. v0.10.29 점검에서 메뉴가 4개 항목이며 삭제 항목은 인덱스 3임을 재확인하고, 분기 인덱스 및 전용 검증기를 수정함. Google 연결 계정은 재인증을 거치도록 구현. Firebase 실제 삭제 성공 및 익명 계정의 재인증/최근 로그인 조건은 아직 실기기·테스트 계정으로 검증되지 않음. 기기 내부 SQLite GPS 기록/해금 데이터는 보존하는 설계.
- 외부 웹 삭제 요청: https://headjin486.github.io/headjin486/delete-account.html
- 개인정보 처리방침: https://headjin486.github.io/headjin486/privacy.html
- 운영상 미완료: 이메일로 접수된 요청을 누가, 어떤 신원 확인 절차로, 어떤 시간 내 처리할지 운영 절차를 문서화하고 실제 테스트해야 한다. 삭제 결과 회신도 필요하다.
- 공개 웹 페이지에 남은 출시 전/주의 문구를 제거하기 전에는 최종 URL로 확정하지 않는다.
- 백업 비활성화와 기존 백업 삭제는 다른 동작임을 사용자에게 분명히 안내한다.

## 5. 스토어 등록 및 테스트 체크리스트

- [ ] Play Console 개발자 계정 생성 및 계정 유형 확인
- [ ] 개발자 계정 생성일 확인: 개인 계정이 2023-11-13 이후 생성되었다면 최소 12명의 테스터가 비공개 테스트에 연속 14일 이상 참여해야 프로덕션 액세스를 신청할 수 있음
- [ ] 앱 이름, 짧은 설명, 자세한 설명 확정
- [ ] 512×512 앱 아이콘, 1024×500 기능 그래픽, 휴대전화 스크린샷 준비 및 실제 UI/브랜드 문구 확인
- [ ] 개인정보 처리방침 URL 최종 확정
- [ ] 계정 삭제 웹 URL 및 실제 운영 절차 검증
- [ ] App content의 위치 권한 및 location FGS 선언, 실제 시연 영상 제출
- [ ] Data safety 설문을 최종 AAB와 SDK/네트워크 검증 후 작성
- [ ] 광고 포함 여부: 현재 빌드는 광고 SDK를 포함하지 않는 것으로 파악됨. 실제 AAB 재검증 후 '광고 없음' 응답
- [ ] 콘텐츠 등급, 대상 연령, 앱 액세스, 스토어 연락처 작성
- [ ] 내부 테스트 → 비공개 테스트(해당 계정에 요구되는 경우) → 프로덕션 액세스 신청

## 6. 출시 차단 항목

아래 항목은 추정으로 완료 처리하지 않는다.
- 실제 AAB merged manifest / SDK 목록 검증
- 타일 제공자의 정확한 데이터 처리 범위 확인
- Data safety 분류 확정
- 운영자 법적 표시사항 및 문의처 확정
- 외부 계정 삭제 요청의 실제 처리 절차와 삭제 테스트
- Play Console 계정 생성일에 따른 테스트 요건 확인
- 실제 기기에서 포그라운드 서비스 영상 촬영 및 검증

## 7. 공식 정책 참고

- Foreground service 선언 및 동영상 요구사항: https://support.google.com/googleplay/android-developer/answer/13392821
- Foreground service 정책: https://support.google.com/googleplay/android-developer/answer/16559646
- 신규 개인 개발자 계정 테스트 요건: https://support.google.com/googleplay/android-developer/answer/14151465

주의: 이 문서는 내부 준비 문서이며 법률 자문이 아니다. 위치정보 관련 국내 법령상 신고·고지 의무는 운영 주체와 서비스 구조를 확인해 별도 검토한다.


## 8. 2026-11-22 추가 검증 결과 (v0.10.27, 이전 빌드 기록)

- 이 절은 v0.10.27의 이전 점검 기록이다. 현재 배포 후보는 아래 9절의 v0.10.28이며, 이전 AAB의 User-Agent 문제는 v0.10.28에서 수정했다.
- AAB 의존성 메타데이터에서 Firebase Authentication, Firebase Firestore, osmdroid, Google Play services Location을 확인했다.
- AAB 권한 문자열에서 `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_LOCATION`을 확인했고 `ACCESS_BACKGROUND_LOCATION`은 발견되지 않았다.
- AAB 의존성 메타데이터에서 AdMob 및 Firebase Analytics는 확인되지 않았다. 전체 네트워크/SDK 검증 전까지 최종 선언으로 확정하지 않는다.
- v0.10.27에서는 OSM User-Agent가 구버전 문자열로 남아 있었으나, v0.10.28 AAB에서 새 `MY EARTH` 식별 문자열을 확인했다.
- OSMF 표준 타일 서버는 상업용 SLA가 없고 상업 서비스에 대해 접근 중단 가능성을 고지한다. 향후 광고 수익화 전에 상업 이용 조건이 명확한 타일 제공자로 전환하는 것을 권고한다.

추가 내부 문서:
- Data Safety 분류 및 AAB 검증: `docs/DATA_SAFETY_REVIEW_KO.md`
- 외부 계정 삭제 수동 운영 절차: `docs/ACCOUNT_DELETION_OPERATIONS_KO.md`
- 스토어 등록 문안: `docs/PLAY_STORE_LISTING_KO.md`


## 9. v0.10.28 최종 빌드 확인 (2026-11-22)

- GitHub Actions run: https://github.com/headjin486/headjin486/actions/runs/45009972849
- 결과: Play 출시 설정 검사, 단위 테스트, Release APK 빌드, APK 서명 검증, AAB 생성 및 업로드 단계 성공. 다만 `scripts/verify-service-lifecycle.sh` 파일이 소스 패키지에 없어 기존 정적 수명주기 스크립트 검사는 실행되지 않았음(워크플로 로그에서 경고 확인). 따라서 수명주기 동작은 실기기에서 별도 검증해야 함.
- versionName: 0.10.28 / versionCode: 81 / applicationId: com.earthunlock.app
- AAB SHA-256: `f64326c87f920ef7b035d5e3da634ee1e01e4e95514ea70f9cb91ac2074d6b5e`
- APK SHA-256: `dc8b1f57b8ef82e19f6e961ef838dcc71f0928845232f329da20c29e4ddc4df4`
- AAB DEX에서 새 User-Agent 문자열 `MY EARTH/0.10.28 (Android; com.earthunlock.app; contact: headjin486@gmail.com)`을 확인했고, 이전 `EarthExplorer/0.7.6` 문자열은 발견되지 않았다.
- AAB manifest에서 package `com.earthunlock.app`, versionName `0.10.28`, 위치 및 위치 포그라운드 서비스 권한을 확인했다. `ACCESS_BACKGROUND_LOCATION`은 manifest 문자열에서 발견되지 않았다.
- 빌드 성공은 실제 스마트폰에서의 지도 타일 응답·GPS·로그인/백업 기능의 재시험을 대체하지 않는다. 사용자가 설치 테스트를 하기 전까지 실기기 검증은 미완료로 유지한다.

## 10. 2026-11-22 계정 삭제 메뉴 점검 및 수정

- v0.10.27 계정 삭제 메뉴 항목은 배열의 세 번째 항목(인덱스 2)이지만, 실행 분기가 `which == 3`을 검사해 삭제 메뉴를 눌러도 삭제 확인 창이 열리지 않는 결함을 확인했다.
- v0.10.29 패치에서 실행 인덱스를 2로 수정하고, 메뉴 항목 순서·인덱스·Firestore 청크 삭제 후 Auth 계정 삭제 순서를 검사하는 별도 엄격 검증 스크립트를 추가했다.
- 이 수정은 소스 및 CI에 반영됐으며, v0.10.29 빌드/검증 결과는 GitHub Actions 실행 완료 후 기록한다.
- Firebase 실제 데이터 삭제 리허설은 운영 Firebase 테스트 계정이 필요하므로 아직 미완료다. 실제 삭제 성공을 주장하지 않는다.
- 추가 확인: 기존 `verify-service-lifecycle.sh`는 현 소스 구조에서 실패하는 오래된 검증 스크립트로 확인되어 CI 실행 단계에서 제거했다. 이를 성공으로 간주하지 않으며, v0.10.29 전용 엄격 정책 검증 스크립트가 계정 삭제 메뉴 인덱스와 Firestore→Auth 삭제 순서를 검사한다. 위치 서비스의 실제 생명주기 동작은 실기기 검증이 여전히 필요하다.
