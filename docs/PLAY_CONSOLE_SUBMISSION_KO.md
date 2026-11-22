# MY EARTH Google Play 제출 준비서

최종 점검일: 2026-11-22
앱: MY EARTH
패키지: com.earthunlock.app
현재 검증 빌드: v0.10.33 / versionCode 86
compileSdk / targetSdk: 36 / 36
상태: 개발자 신원 확인 및 출시 필수 검증 진행 중

## 1. 제품 설명

MY EARTH는 사용자가 실제로 지나온 길과 장소를 개인 지도로 보존하는 탐험 기록 앱이다. 걷기 목표나 순위 경쟁이 아니라, 사용자가 걸어온 길을 소중하게 남기는 것이 핵심 가치다.

스토어 문구:
- 앱 이름: MY EARTH
- 간단한 설명: 내가 걸어온 길을 기록하고, 지나온 곳을 나만의 지도로 남겨보세요.
- 슬로건: 내가 걸어온 길, 나만의 지도가 되다.
- 영어 슬로건: YOUR FOOTSTEPS. YOUR WORLD.

## 2. 검증 빌드

- versionName: 0.10.33
- versionCode: 86
- applicationId: com.earthunlock.app
- targetSdk: 36
- GitHub Actions 성공 실행: https://github.com/headjin486/headjin486/actions/runs/45029892659
- APK SHA-256: 4edd25a688163c18b764e6453eae854f048178902f0fcd91c1487442ce44feb0
- AAB SHA-256: fdbb4762795dfa6e9d1575ca0a46da2e39bfc1f5ee739fcc139c9ccadc0e095d
- 기존 서명 인증서 지문과 APK 서명 일치 확인 통과.
- AAB JAR 서명 검증 통과.
- 단위 테스트 및 Android Release APK/AAB 빌드 통과.
- 패키지 ID, 버전, 위치 FGS, cleartext false, 백그라운드 위치 권한 미선언 정적 검사 통과.

이 검증은 Play Console 정책 승인, Firebase 운영 테스트, 실기기 기능 검증 전체 완료를 의미하지 않는다.

## 3. 위치 포그라운드 서비스 선언

- 서비스 유형: location.
- 권한: ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, FOREGROUND_SERVICE, FOREGROUND_SERVICE_LOCATION.
- ACCESS_BACKGROUND_LOCATION은 선언하지 않음.
- 사용자가 직접 탐험을 시작한 동안 다른 앱 사용 또는 화면 잠금 상태에서도 경로 기록을 이어가기 위해 location foreground service를 사용한다.
- 실행 중 지속 알림을 표시하며 앱 또는 알림에서 중지할 수 있다.
- Play Console 위치/FGS 선언과 시연 영상은 실제 v0.10.33 기기 화면으로 작성한다. 실제 영상은 아직 미확보 상태로 유지한다.

## 4. Data Safety

Data Safety 설문은 별도 내부 문서 `docs/DATA_SAFETY_REVIEW_KO.md`를 기준으로 진행한다.
잠정 분류 후보:
- 정확한 위치: 선택형 클라우드 백업의 5m 격자 셀 식별자.
- 이메일 주소: Google 계정 연결 시 Firebase Auth가 처리할 수 있는 이메일.
- 사용자 ID: Firebase UID.
- OSM 타일 요청에서 처리되는 IP/요청 영역 정보는 추가 확인 후 분류.
원본 GPS 경로, 측정 시각, 위치 정확도는 기기 내부 저장이며 클라우드 백업 payload에 포함하지 않는다.

## 5. 계정 삭제 및 개인정보

- 개인정보 처리방침: https://headjin486.github.io/headjin486/privacy.html
- 계정 삭제 요청 페이지: https://headjin486.github.io/headjin486/delete-account.html
- 외부 삭제 요청은 이메일 접수 후 운영자가 수동 처리하는 방식이다. Google Play는 자동화된 삭제 시스템만을 요구하지 않으며, 이메일 기반 웹 요청 경로도 허용한다. 다만 실제로 요청을 확인하고 관련 계정·데이터를 삭제할 운영 체계가 필요하다.
- 인앱 삭제 경로는 구현되어 있으나 운영 Firebase에서 Google 재인증 및 Auth/Firestore 전체 삭제 성공을 아직 검증하지 않았다.
- 삭제 페이지의 메일 수신, 계정 소유 확인, 합리적인 처리 기한, 완료 회신 및 실패 대응을 실제로 리허설하기 전에는 출시 차단 항목으로 유지한다.
- 개인정보 처리방침은 출시 전 초안 문구와 운영자 공개정보를 확정하고 실제 앱/SDK와 일치시킨다.

## 6. 스토어 그래픽 및 메타데이터

- [ ] 512×512 앱 아이콘 최종 출력본 확인.
- [ ] 1024×500 기능 그래픽 제작 및 검수.
- [ ] 실제 v0.10.33 휴대전화 스크린샷 준비.
- [ ] 스크린샷에 테스트 계정/개인 닉네임/개인 위치가 노출되지 않는지 확인.
- [ ] 앱 이름, 간단한 설명, 자세한 설명 최종 확정.
- [ ] 연락처 이메일 및 개발자 공개정보 확인.
- [ ] 콘텐츠 등급, 대상 연령, 광고 포함 여부, 앱 액세스 정보 작성.
- [ ] Data Safety 및 데이터 삭제 질문 작성.

## 7. 계정 및 테스트 요구

- Google Play 개발자 신원 확인: 사용자 완료 통보 대기.
- 개인 개발자 계정 생성일을 확인한다. 2023-11-13 이후 생성된 개인 계정이면 프로덕션 액세스 전에 비공개 테스트 12명 이상, 연속 14일 참여 요건이 적용될 수 있으므로 Play Console의 현재 계정 안내를 확인한다.
- 앱 패키지명 등록/검증 등 Play Console의 계정별 요구사항을 확인한다.
- Play 리뷰용 로그인/앱 접근이 필요하다면 테스트 전용 계정과 안전한 심사 안내를 준비한다. 비밀번호/인증코드를 일반 메모나 공개 문서에 기록하지 않는다.

## 8. 출시 차단 항목

- [ ] 개발자 신원 확인 완료.
- [ ] 운영 Firebase 테스트 계정으로 Google OAuth / 계정 연결 / 복원 확인.
- [ ] 백업 동의 거부 상태에서 Firestore 쓰기가 없는지 확인.
- [ ] 계정 삭제 테스트 계정 리허설: Firestore 청크 및 Firebase Auth UID 모두 삭제 확인.
- [ ] 익명 계정의 최근 로그인 요구 및 부분 실패 처리 확인.
- [ ] 외부 삭제 이메일 접수·소유 확인·처리·회신 운영 절차 검증.
- [ ] 최신 AAB의 전체 SDK 및 실제 외부 네트워크 수신자 확인.
- [ ] Data Safety 최종 답변 확정.
- [ ] 개인정보 처리방침의 운영자/문의처/보유기간/삭제 절차 확정.
- [ ] 위치 포그라운드 서비스 실제 기기 시연 영상 촬영.
- [ ] 스토어 그래픽 및 메타데이터 완성.
- [ ] Play Console 계정별 테스트 요건 확인 및 수행.

## 9. 운영상 고정 원칙

- 기존 package ID, signing key, SQLite 탐험 데이터 구조를 변경하지 않는다.
- 기존 사용자 데이터 보존을 우선하며, 사용자 동의 없는 초기화/삭제/마이그레이션을 하지 않는다.
- Firebase Spark 무료 플랜만 사용한다. Blaze 전환, Cloud Functions 추가, 결제 계정 연결은 별도 승인 전까지 하지 않는다.
- 원본 GPS 및 시간순 경로를 서버에 업로드하지 않는다.
- 글로벌 순위/경쟁 기능을 초기 출시 범위에 추가하지 않는다.
