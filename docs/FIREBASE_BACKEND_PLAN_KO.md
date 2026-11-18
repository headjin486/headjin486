# EARTH UNLOCK Firebase 백엔드 설계

## 목표
- Firebase Spark(무료)로 시작한다. 유료 요금제로 자동 전환하지 않는다.
- 앱 첫 실행 시 익명 Firebase 계정을 발급하고 닉네임을 등록한다.
- 랭킹은 전 세계 누적 해금 면적 기준 TOP 30과 내 순위를 제공한다.
- GPS 원본 좌표/이동 경로는 공개하지 않는다.
- SQLite의 explored_cells가 기기 내 탐험 데이터의 기준 데이터다.

## 데이터 구조 (Cloud Firestore)

### profiles/{uid}
- nickname: 공개 닉네임
- nicknameNormalized: 중복 확인용 정규화 문자열
- createdAt: 서버 타임스탬프
- updatedAt: 서버 타임스탬프
- recoveryProvider: 연결된 복구 수단 종류(예: google, none)

### nickname_claims/{nicknameNormalized}
- uid: 해당 닉네임 소유자 UID
- createdAt: 서버 타임스탬프
- 이 컬렉션은 Cloud Functions만 쓰도록 제한한다.
- 닉네임 등록/변경은 트랜잭션으로 중복을 방지한다.

### leaderboard/{uid}
- nickname: 랭킹 표시용 닉네임 스냅샷
- exploredAreaM2: 서버가 검증한 누적 해금 면적
- exploredCellCount: 중복 제거된 해금 격자 수
- updatedAt: 서버 타임스탬프
- 클라이언트 직접 쓰기를 금지하고 Cloud Functions만 갱신한다.

### exploration_backups/{uid}/chunks/{chunkId}
- 압축된 격자 셀 식별자와 버전 정보
- GPS 점/시간순 이동 경로는 저장하지 않는다.
- 복구 목적의 사용자 데이터이며 공개 랭킹 쿼리에서 제외한다.
- 업로드/다운로드는 인증된 사용자 본인만 허용한다.

## 인증 및 첫 실행
1. Firebase Authentication 익명 로그인으로 UID를 만든다.
2. 닉네임 설정 화면에서 닉네임을 제출한다.
3. Callable Cloud Function이 형식/금칙어/중복을 검사하고 닉네임을 원자적으로 예약한다.
4. 사용자가 원하면 Google 계정을 익명 계정에 연결해 기기 변경 복구 수단을 만든다.
5. Google 연결 전에도 현재 기기에서는 탐험할 수 있지만, 앱 데이터 삭제/기기 분실 시 복구가 보장되지 않는다는 점을 안내한다.

## 랭킹 및 면적 검증
- TOP 30은 leaderboard를 exploredAreaM2 내림차순으로 조회한다.
- 내 순위는 동일한 점수 정렬 규칙(면적 내림차순, UID 오름차순)을 사용해 계산한다.
- 점수는 클라이언트가 임의로 쓰지 못하게 한다.
- 복구용 셀 데이터의 중복을 제거하고, 서버 측 계산/검증 후 집계한다.
- 앱은 5m 격자 셀을 사용하므로 서버에서도 동일한 격자 좌표계와 위도별 셀 면적 공식을 적용해야 한다.
- 서버 검증 전에는 랭킹 점수를 '검증 중'으로 표시하고, 검증되지 않은 클라이언트 수치를 공식 점수로 취급하지 않는다.

## 보안 규칙 초안
- 모든 데이터 접근은 Firebase Authentication UID 기준으로 제한한다.
- profiles는 랭킹 표시를 위해 읽기 허용하되 쓰기는 Cloud Functions로 제한한다.
- leaderboard는 읽기만 허용하고 클라이언트 쓰기는 전면 금지한다.
- nickname_claims는 클라이언트 읽기/쓰기 모두 금지한다.
- exploration_backups는 인증된 본인 UID 경로만 읽기/쓰기 허용한다.
- Firebase App Check를 활성화하고 업로드 크기/빈도를 제한한다.

## 복구 정책
- 앱 실행/탐험 중 일정 간격 또는 새 셀 누적량 기준으로 백업을 동기화한다.
- 재설치/새 기기에서는 Google 로그인 후 서버의 셀 백업을 내려받아 SQLite explored_cells에 병합한다.
- 로컬 DB를 서버 백업으로 덮어쓰지 않고 합집합(INSERT OR IGNORE)으로 병합한다.
- 네트워크 오류가 나도 로컬 탐험은 계속되고, 동기화는 재시도한다.

## 출시 전 필수 작업
- Firebase 프로젝트 생성 및 Android 앱 등록
- google-services.json 추가(저장소에 비밀/개인 설정 파일을 공개하지 않도록 관리)
- Authentication 익명 로그인 및 Google 연결 활성화
- Firestore 데이터베이스 생성
- Cloud Functions 배포 및 Firestore 보안 규칙 적용
- 개인정보 처리방침에 계정/닉네임/랭킹/백업 데이터 수집·보관·삭제 항목 추가
- 계정 삭제 및 서버 데이터 삭제 기능 제공
- Google Play 데이터 보안(Data safety) 항목과 개인정보 처리방침 일치 확인

## 구현 순서
1. 고정 서명키 기반 업데이트 경로를 검증한다.
2. 닉네임 온보딩과 로컬 프로필 저장을 추가한다.
3. Firebase 프로젝트 연결 및 익명 인증을 추가한다.
4. 닉네임 중복 방지 Cloud Function과 랭킹 읽기 기능을 추가한다.
5. 셀 백업/복구와 서버 검증 집계를 추가한다.
6. 개인정보/계정 삭제 및 Play 내부 테스트를 완료한다.
