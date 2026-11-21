# MY EARTH Firebase 연결 단계 (Spark 무료 단계)

## 현재 확인된 상태
- Android 패키지 ID: com.earthunlock.app
- Firebase Android 앱 등록 및 google-services.json 다운로드 완료
- GitHub Actions Secret GOOGLE_SERVICES_JSON 등록 완료(사용자 확인)
- 빌드 워크플로에서 설정 파일을 앱 모듈에 배치하고 Google Services 플러그인을 적용하도록 구성
- 앱의 Firebase 익명 인증·Firestore 백업 코드는 아직 구현/검증 단계다.
- 기존 로컬 탐험 데이터는 유지한다. 앱 삭제나 데이터 초기화는 하지 않는다.

## Firebase Console에서 사용자가 설정할 항목
1. Firebase Console → Build → Authentication → Get started
2. Sign-in method에서 Anonymous를 활성화하고 저장한다.
3. Build → Firestore Database → Create database를 선택한다.
4. 처음에는 Production mode를 선택하고, 실제 운영 지역을 고려해 위치를 결정한다.
5. Firestore Rules 탭에는 저장소의 firebase/firestore.rules를 테스트한 뒤 적용한다. 아직 앱 연동 검증 전에는 임의로 넓은 공개 규칙을 적용하지 않는다.
6. Google 로그인은 추후 단계에서 설정한다. 그때 SHA-1/SHA-256 지문과 OAuth 구성을 확인한다.

## 데이터·비용 보호
- Spark 무료 요금제만 사용한다. Blaze 전환 및 결제 계정 연결은 별도 동의 없이 하지 않는다.
- Google Analytics는 현재 추가하지 않는다.
- Firebase에 업로드할 대상은 5m 해금 셀 식별자뿐이다. GPS 좌표와 시간순 이동 경로는 업로드하지 않는다.
- Google 계정 연결 전 익명 UID는 기기 분실·앱 데이터 삭제 시 복구할 수 없으므로 앱에서 경고한다.
- 앱 데이터 삭제/재설치 또는 기존 앱 제거를 아직 하지 않는다.

## 구현·검증 순서
1. 익명 인증 UID 생성 및 앱 재실행 후 동일 UID 유지
2. 기존 SQLite explored_cells의 5m 셀을 압축 청크로 백업
3. 클라우드 청크를 기존 SQLite에 합집합 병합하고 면적 통계 재계산
4. 네트워크 차단/복구 시 로컬 사용 지속 및 동기화 재시도
5. 기존 익명 계정을 Google 계정에 연결
6. 새 기기/재설치 복원과 계정 삭제를 테스트
7. 개인정보 처리방침 및 Google Play Data safety 응답을 실제 데이터 흐름과 일치시킴

## 출시 차단 항목
- Google 계정 연결·복원 실기기 테스트
- 계정 삭제 시 Firebase Auth 사용자 및 백업 청크 전체 삭제
- Firestore 보안 규칙 Emulator 테스트
- Firebase App Check 적용
- 개인정보 처리방침, 데이터 보유·삭제 기준 및 Play Data safety 검증
