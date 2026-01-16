import os
import sys
import subprocess
import shutil

# [NEW] .env 파일 로드 기능 추가
try:
    from dotenv import load_dotenv
except ImportError:
    print("\n\033[91m[ERROR] 'python-dotenv' 라이브러리가 설치되지 않았습니다.\033[0m")
    print("아래 명령어로 설치 후 다시 실행해주세요:")
    print("pip install python-dotenv\n")
    sys.exit(1)

# .env 파일 로드 (현재 디렉토리 기준)
load_dotenv()

# ==========================================
# 설정 (환경 변수 우선, 없으면 기본값)
# ==========================================

# GCP 프로젝트 ID (필수)
# .env 파일의 'PROJECT_ID' 또는 시스템 환경변수 'GCP_PROJECT_ID'를 찾습니다.
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("PROJECT_ID") or "your-project-id-here"

# 서버 포트 (기본값 8000)
DEPLOY_SERVER_PORT = os.getenv("DEPLOY_SERVER_PORT", "8000")

# 리전 설정 (.env의 LOCATION 또는 기본값 asia-southeast1)
REGION = os.getenv("LOCATION", "asia-southeast1")

# 이미지 및 서비스 이름 설정
IMAGE_NAME = os.getenv("IMAGE_NAME", "DOCKER_IMAGE_NAME")
SERVICE_NAME = os.getenv("SERVICE_NAME", "CLOUD_RUN_SERVICE_NAME")
GCR_HOST = os.getenv("GCR_HOST", "asia.gcr.io") # Google Container Registry

# ==========================================
# 유틸리티 함수
# ==========================================
def print_step(message):
    print(f"\n\033[96m[STEP] {message}\033[0m")

def print_error(message):
    print(f"\n\033[91m[ERROR] {message}\033[0m")

def run_command(command, shell=False):
    """쉘 명령어를 실행하고 에러 발생 시 종료합니다."""
    try:
        # 리스트 형태의 명령어를 문자열로 보여줌
        cmd_str = command if isinstance(command, str) else " ".join(command)
        print(f"🚀 Executing: {cmd_str}")
        
        subprocess.check_call(command, shell=shell)
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print_error(f"Command not found. Please check if gcloud and docker are installed.")
        sys.exit(1)

def check_requirements():
    """gcloud와 docker가 설치되어 있는지 확인합니다."""
    if not shutil.which("gcloud"):
        print_error("Google Cloud SDK (gcloud) is not installed.")
        sys.exit(1)
    if not shutil.which("docker"):
        print_error("Docker is not installed.")
        sys.exit(1)

# ==========================================
# 메인 로직
# ==========================================
def main():
    check_requirements()

    # 프로젝트 ID 확인
    if not GCP_PROJECT_ID or GCP_PROJECT_ID == "your-project-id-here":
        print_error("GCP_PROJECT_ID (or PROJECT_ID) is not set in .env file.")
        sys.exit(1)

    print(f"🔥 Starting deployment for Project: {GCP_PROJECT_ID}")
    print(f"   - Region: {REGION}")
    print(f"   - Port: {DEPLOY_SERVER_PORT}")
    
    # 1. GCP 프로젝트 설정
    print_step("Setting GCP Project Configuration")
    run_command(["gcloud", "config", "set", "project", GCP_PROJECT_ID])
    
    # 2. Docker 빌드
    print_step("Building Docker Image")
    # 기존 이미지 제거 (오류 무시)
    subprocess.run(["docker", "rmi", "-f", IMAGE_NAME], stderr=subprocess.DEVNULL)
    
    # Docker 빌드 실행
    run_command([
        "docker", "build", 
        "--build-arg", f"SERVER_PORT={DEPLOY_SERVER_PORT}", 
        "-t", IMAGE_NAME, 
        "-f", "Dockerfile.detached", 
        "."
    ])

    # 3. Docker 인증 및 태깅, 푸시
    print_step("Configuring Docker & Pushing to GCR")
    
    # 리전 설정
    run_command(["gcloud", "config", "set", "compute/region", REGION])
    
    # Docker 인증 헬퍼 설정
    run_command(["gcloud", "auth", "configure-docker", "-q"]) # -q for quiet mode

    # 전체 이미지 태그 생성 (asia.gcr.io/PROJECT_ID/IMAGE_NAME:latest)
    full_image_tag = f"{GCR_HOST}/{GCP_PROJECT_ID}/{IMAGE_NAME}:latest"

    # 기존 리모트 이미지 제거 시도 (선택 사항, 로컬 정리용)
    subprocess.run(["docker", "rmi", "-f", full_image_tag], stderr=subprocess.DEVNULL)

    # 태깅
    run_command(["docker", "tag", IMAGE_NAME, full_image_tag])
    
    # 푸시
    run_command(["docker", "push", full_image_tag])

    # 4. Cloud Run 배포
    print_step("Deploying to Cloud Run")
    run_command([
        "gcloud", "run", "deploy", SERVICE_NAME,
        "--image", full_image_tag,
        "--platform", "managed",
        "--region", REGION,
        "--allow-unauthenticated",
        "--port", DEPLOY_SERVER_PORT
    ])

    # 5. 권한 설정 (IAM Policy)
    print_step("Setting IAM Policy (Public Access)")
    run_command([
        "gcloud", "beta", "run", "services", "add-iam-policy-binding", SERVICE_NAME,
        "--region", REGION,
        "--member=allUsers",
        "--role=roles/run.invoker"
    ])

    print("\n\033[92m✅ Deployment Completed Successfully!\033[0m")

if __name__ == "__main__":
    main()
