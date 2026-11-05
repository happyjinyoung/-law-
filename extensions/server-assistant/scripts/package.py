"""명시된 소스·가상 평가·제출 자료만 ZIP으로 묶는다. DB·키·업로드·캐시는 제외."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
DIRECTORIES={'backend','frontend','docs','evaluation','samples','tests','scripts','submission'}
FILES={'server.py','README.md','.env.example','.gitignore','requirements.txt','requirements-dev.txt','package.json','package-lock.json'}


def package():
    destination=ROOT.parent/'naesoneul-java-github.zip'
    included=[]
    with ZipFile(destination,'w',ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob('*')):
            relative=path.relative_to(ROOT)
            if not path.is_file() or '__pycache__' in relative.parts:continue
            if relative.parts[0] not in DIRECTORIES and str(relative) not in FILES:continue
            if path.suffix.lower() in {'.pyc','.db','.sqlite','.sqlite3','.log'}:continue
            if path.name.startswith('.env') and path.name!='.env.example':continue
            archive.write(path,Path(ROOT.name)/relative);included.append(relative.as_posix())
    assert not any(p.startswith(('data/','uploads/','work/','.git/')) or p=='.env' for p in included)
    print(f'{destination}\n{len(included)} files / {destination.stat().st_size} bytes')


if __name__=='__main__':package()
