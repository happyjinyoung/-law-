"""python verify_originals.py: ZIP에서 가져온 원본 5개가 바뀌지 않았는지 검사."""
from run import verify_originals
if __name__=='__main__':print(f'SHA-256 일치: 배포 파일 {verify_originals()}개 (원본 4개 보존, HTML 화면 분리 CSS만 추가)')
