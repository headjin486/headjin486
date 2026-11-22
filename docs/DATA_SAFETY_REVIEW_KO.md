# MY EARTH Data Safety 사전 점검표

최종 점검일: 2026-11-22
대상 빌드: v0.10.33 / versionCode 86
패키지: com.earthunlock.app
AAB SHA-256: fdbb4762795dfa6e9d1575ca0a46da2e39bfc1f5ee739fcc139c9ccadc0e095d

> 내부 검토 문서이며 Play Console 설문 최종 답변이 아니다. 운영 Firebase의 실제 계정·네트워크·삭제 리허설 전에는 확정 제출하지 않는다.

## 1. 현재 빌드에서 확인된 사항

- GitHub Actions 실행 #45029892659 성공.
- versionName 0.10.33 / versionCode 86 / compileSdk 36 / targetSdk 36.
- APK 서명 검증과 기존 업로드 인증서 지문 일치 확인 통과.
- AAB 생성 및 로컬 JAR 서명 검증 통과.
- 패키지 ID `com.earthunlock.app`.
- Manifest에서 ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, FOREGROUND_SERVICE, FOREGROUND_SERVICE_LOCATION 확인.
- ACCESS_BACKGROUND_LOCATION 미선언, cleartext traffic 비활성화, 위치 포그라운드 서비스 비공개(exported=false) 확인.
- Firebase Authentication, Firebase Cloud Firestore, osmdroid, Google Play services Location 사용.
- AdMob 및 Firebase Analytics 의존성은 이전 AAB 메타데이터 점검에서 확인되지 않았으나, 최신 AAB 전체 SDK/네트워크 트래픽 분석 전까지 최종 선언으로 단정하지 않는다.
- 표준 지도 타일 엔드포인트는 `https://tile.openstreetmap.org/`이며 User-Agent에 MY EARTH, 패키지, 문의 이메일을 식별하도록 구성.
- 앱의 백업 동의는 Google 계정 연결과 별도 단계다. Google 계정 연결만으로 자동 백업 동의를 대신하지 않는다.
- 클라우드 백업 payload는 해금된 5m 격자 셀 ID만 포함하며 원본 GPS 좌표·시간순 경로·GPS 측정 시각은 포함하지 않는다.
- Firebase UID별 Firestore 경로는 소유자 인증을 요구하고 허용 필드를 제한한다.

## 2. Play Console 데이터 유형 후보

| 데이터 유형 | 후보 수집 여부 | 선택 여부 | 목적 | 근거 및 주의 |
|---|---|---|---|---|
| 위치 - 정확한 위치 | 예 | 선택적 | 앱 기능, 백업/복원 | 백업 동의 시 5m 격자 셀 식별자가 Firebase로 전송됨. 원본 GPS 경로는 로컬 전용. 셀 좌표가 실제 위치를 좁게 특정할 수 있어 위치 데이터로 신고하는 보수적 분류 |
| 개인 정보 - 이메일 주소 | 예(해당 시) | 선택적 | 계정 관리 | 이용자가 Google 계정을 연결하면 Firebase Auth가 Google 계정 이메일을 처리할 수 있음. 실제 운영 Auth 사용자 레코드 필드 확인 필요 |
| 기기 또는 기타 ID - 사용자 ID | 예(해당 시) | 선택적 | 계정 관리, 백업/복원 | Firebase UID가 계정과 백업 문서를 연결. 실제 인증 시점과 Firebase 전송 내용을 확인할 것 |
| 기기 또는 기타 ID - 기타 식별자/IP 관련 정보 | 미확정 | 미확정 | 지도 타일 요청 | OSM 타일 서버는 통상 네트워크 IP 및 요청 타일 정보를 볼 수 있음. Google Data Safety 분류 여부는 최신 SDK/트래픽과 해당 데이터 유형 정의를 대조한 뒤 결정 |

로컬에만 저장되고 기기 밖으로 전송되지 않는 원본 GPS 경로, 탐험 통계, 닉네임은 Google Play의 '수집'으로 자동 분류하지 않는다. 다만 앱 내 개인정보 처리방침에는 로컬 처리 사실을 계속 공개한다.

## 3. Play Console 설문에 대한 잠정 방향

- 앱이 수집 또는 공유하는 데이터가 있는가: **예**로 진행하는 것이 안전하다.
- 전송 중 암호화: Firebase 및 지도 타일 요청은 HTTPS/TLS 사용을 전제로 하나, 최신 AAB의 모든 네트워크 요청을 확인한 후 확정.
- 계정/데이터 삭제 요청 수단: 인앱 계정 삭제 경로와 외부 이메일 요청 페이지가 존재한다. 다만 운영 Firebase 테스트 계정으로 전체 삭제 성공을 검증하지 못했으므로 최종 제출 전 리허설 필수.
- Firebase는 데이터 처리 서비스 제공자로 분류할 수 있는지 Google의 service provider 정의 및 실제 계약·처리관계를 확인한다. 서비스 제공자 예외가 sharing 분류에 영향을 주더라도 collection 사실을 누락하지 않는다.
- 데이터 유형별 사용 목적, 필수/선택, 보유기간은 앱 실제 흐름과 일치시킨다.
- Play Console Data Safety는 SDK가 전송하는 데이터도 포함한다. 모든 SDK와 외부 수신자를 확인한다.

## 4. 아직 끝나지 않은 검증

1. 테스트 전용 Google 계정으로 실제 Firebase Auth 로그인·연결을 수행하고 email, displayName, providerData, UID 필드를 확인.
2. 백업 동의 전/후 Firestore 쓰기와 네트워크 트래픽을 비교. 동의 거부 시 셀 데이터 쓰기가 없어야 함.
3. Google 계정 연결만으로 백업이 켜지지 않는지 확인.
4. 테스트 계정에서만 여러 백업 청크를 생성하고 앱 내 계정 삭제, Firestore 청크 삭제, Firebase Auth 삭제가 모두 완료되는지 확인.
5. Google 재인증 취소/실패, 네트워크 실패, Auth 삭제 실패에서 부분 삭제와 사용자 안내를 확인.
6. OSM 타일 요청과 Firebase 외의 외부 수신자 및 SDK 전송 데이터를 최신 AAB/실기기에서 확인.
7. 개인정보 처리방침의 운영자 표시, 보유·삭제, 외부 서비스 안내를 실제 운영 방식과 대조.
8. 삭제 이메일을 실제 수신할 수 있는지, 요청 접수·소유 확인·삭제·완료 회신 절차를 테스트.

## 5. 계정 삭제 위험

- Firebase Emulator 기반 규칙 테스트 4건 및 계정 삭제 통합 테스트 2건은 통과했으나, 이는 운영 Firebase 프로젝트 검증이 아니다.
- 현재 삭제 구현은 해당 UID의 Firestore 청크를 먼저 삭제하고 Auth 사용자를 삭제한다. Auth 삭제가 실패하면 백업은 이미 삭제됐지만 계정은 남는 부분 실패가 가능하다.
- v0.10.33은 삭제 실패 후 자동 백업을 중지하고 사용자에게 실패 상태를 알린다. 이미 삭제된 백업을 복원하지는 않는다.
- Firebase Android SDK 문서상 `FirebaseUser.delete()`의 최근 로그인 요구 예외는 익명 사용자에게 적용되지 않는다. 익명 계정은 재인증 없이 삭제되는 것이 예상 동작이며, 실제 앱과 운영 Firebase 테스트로 확인한다. Google 계정은 재인증이 필요하다.
- 실제 사용자 계정이나 실제 탐험 데이터로 삭제 테스트하지 않는다.

## 6. 외부 서비스 / 타일 서버

- Firebase Authentication: 익명 인증 및 선택적 Google 계정 연결.
- Firebase Cloud Firestore: 선택 동의 후 해금 지도 셀 백업.
- OpenStreetMap 표준 타일 서버: 지도 타일 제공. 요청 IP 및 요청 타일 영역 등 네트워크 운영정보가 처리될 수 있다.
- OSM 표준 타일 서버는 상업용 SLA를 보장하는 전용 타일 호스팅 상품이 아니다. 향후 광고 등 수익화 전에는 상업적 이용 조건이 명확한 타일 제공자로 전환할지 검토한다.
- 참고: https://operations.osmfoundation.org/policies/tiles/ 및 https://osmfoundation.org/wiki/Privacy_Policy

## 7. 출시 판단

현재 Data Safety는 **초안 상태**다. 최신 AAB 빌드와 서명 검증은 통과했지만, 실제 Firebase 계정 필드, 선택 동의 전후 트래픽, OSM 외부 요청, 운영 계정 삭제, 운영자 처리 절차가 검증되지 않았다. 위 항목이 끝나기 전 Play Console 제출용 답변으로 확정하지 않는다.
