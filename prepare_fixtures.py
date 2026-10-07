"""Build only the authored fixtures used by the component checks."""
import os,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).parent
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
def run(args,**kwargs):subprocess.run(args,cwd=ROOT,check=True,creationflags=FLAGS,**kwargs)
if __name__=='__main__':
    run([sys.executable,'fixtures/create_unity_fixture.py'])
    run([str(ROOT/'windows/dotnet-sdk/dotnet.exe'),'build','fixtures/managed/GameLogic.csproj','-c','Release'])
    run(['docker','exec','-i','modding-lab-analysis','gcc','-x','c','-O0','-g','-o','/tmp/visual-development-fixture','-'],input=(ROOT/'fixtures/native/game_logic.c').read_bytes())
    run(['docker','cp','modding-lab-analysis:/tmp/visual-development-fixture','fixtures/native/game_logic'])
    print('Authored fixtures ready. No commercial game input is included.')
