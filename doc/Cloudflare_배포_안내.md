# Cloudflare Pages 배포 안내

## 자동 배포

`main` 브랜치에 푸시하면 GitHub Actions가 프론트엔드를 빌드한 뒤 **Cloudflare Pages**로 자동 배포합니다.

## 필수 설정 (한 번만)

### 1. Cloudflare Pages 프로젝트 생성

1. [Cloudflare Dashboard](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → **Connect to Git** (또는 Direct Upload만 쓸 경우 생략 가능)
2. **Direct Upload**로 사용할 경우: **Create project** → 프로젝트 이름을 `fashion-agentic-ai`로 생성 (또는 아래 시크릿에서 사용할 이름과 동일하게)

### 2. GitHub 저장소 시크릿 추가

저장소 **Settings** → **Secrets and variables** → **Actions**에서 다음 시크릿을 등록하세요.

| 시크릿 이름 | 설명 | 얻는 방법 |
|------------|------|-----------|
| `CLOUDFLARE_API_TOKEN` | Pages 편집 권한이 있는 API 토큰 | Cloudflare Dashboard → My Profile → API Tokens → Create Token → "Edit Cloudflare Workers" 또는 "Cloudflare Pages Edit" 템플릿 사용 |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 계정 ID | Cloudflare Dashboard → 오른쪽 사이드바 **Account ID** 복사 |

### 3. 프로젝트 이름 변경 (선택)

Cloudflare Pages 프로젝트 이름을 `fashion-agentic-ai`가 아닌 다른 이름으로 쓸 경우,  
`.github/workflows/deploy-cloudflare.yml`의 `projectName` 값을 해당 이름으로 수정하세요.

## 배포 후 URL

배포가 완료되면 다음 주소로 접속할 수 있습니다.

- **https://fashion-agentic-ai.pages.dev**  
  (프로젝트 이름을 바꿨다면 `https://<프로젝트이름>.pages.dev`)

## 참고

- 배포되는 것은 **프론트엔드(React)** 뿐입니다. API(백엔드)는 별도 서버에 두고, 프론트엔드에서 API URL을 해당 서버로 설정해야 합니다.
