# EARTH UNLOCK Firebase 연결 준비 (Spark 무료 단계)

## 현재 상태
- Android applicationId / namespace: `com.earthunlock.app` (v0.8.1부터 고정)
- 앱 내부 닉네임 저장은 구현되어 있지만 Firebase 계정·동기화·랭킹 연결은 아직 미구현
- 아래 Firestore 규칙은 저장소에 준비한 초안이며 Firebase 프로젝트에 아직 배포되지 않음
- Cloud Functions 및 Blaze 결제 요금제는 사용자 별도 승인 전까지 사용하지 않음

## Firebase Console에서 필요한 작업
1. Firebase Console에서 새 프로젝트를 생성한다. Google Analytics는 지금 단계에서 켜지 않아도 된다.
2. Android 앱 추가 시 패키지 이름을 정확히 `com.earthunlock.app`으로 입력한다.
3. `google-services.json`을 내려받는다. 이 파일을 공개 저장소에 올리지 않는다.
4. Authentication에서 익명 로그인을 활성화한다.
5. Firestore Database를 생성하고, 지역은 실제 주요 이용자와 데이터 거주 요구를 고려해 선택한다.
6. 이 저장소의 `firebase/firestore.rules`를 검토한 뒤 Firebase Console Rules에 적용한다.
7. 앱 등록 및 Firestore 설정이 끝나면 Android 구성 파일을 안전하게 빌드 환경에 전달해야 한다.

## 구현·검증 순서
1. 익명 인증으로 UID 발급 및 재실행 시 세션 유지 확인
2. 닉네임 예약 트랜잭션과 중복 닉네임 동시 등록 테스트
3. 기기 내 SQLite explored_cells와 클라우드 백업 청크의 버전/압축 포맷 확정
4. 업로드·복구는 셀 집합 병합(INSERT OR IGNORE)으로 구현하고, 네트워크 실패 시 로컬 탐험을 중단하지 않도록 처리
5. TOP 30 조회와 내 순위 표시 연결
6. 앱 데이터 삭제·새 기기 복구·중복 업로드·오프라인 복귀 테스트

## 비용과 점수 신뢰성
- 이 준비 단계는 Firebase Spark 무료 요금제를 전제로 한다.
- Cloud Functions 배포 또는 Blaze 전환은 하지 않는다.
- Spark에서 클라이언트가 제출하는 탐험 면적은 변조 가능하므로 '잠정 랭킹'으로 표시해야 한다.
- 공식 서버 검증 랭킹이 필요하면 별도 비용·보안 검토와 사용자 승인을 받은 후 진행한다.

## 개인정보 및 출시 차단 항목
- 실제 운영자명과 연락처, 공개 개인정보 처리방침 URL 확정
- 닉네임·계정·탐험 셀 백업의 수집 목적, 보유 기간, 삭제 방법 명시
- 계정 삭제 시 프로필·닉네임 예약·랭킹·백업을 모두 삭제하는 흐름 구현
- Google Play Data safety 응답과 실제 SDK/데이터 흐름 대조
- Firestore 보안 규칙 테스트 및 앱 실기기 복구 테스트
