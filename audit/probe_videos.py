"""Lee cabeceras de todos los vídeos locales; no modifica ni reproduce archivos."""
import concurrent.futures
import json
import pathlib
import subprocess
home = pathlib.Path.home()
lib = pathlib.Path(json.loads((home/'.config/wallpaperengine-picker/config.json').read_text())['steam_library'])
root = lib/'steamapps/workshop/content/431960'
jobs=[]
for folder in sorted(root.iterdir()):
    if not folder.is_dir(): continue
    try: p=json.loads((folder/'project.json').read_text())
    except Exception: continue
    if str(p.get('type','')).lower()=='video' and isinstance(p.get('file'),str):
        jobs.append((folder.name,folder/p['file']))
def probe(job):
    wid,path=job
    try:
        proc=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate:format=duration','-of','json',str(path)],capture_output=True,text=True,timeout=15)
        info=json.loads(proc.stdout or '{}')
        return {'id':wid,'returncode':proc.returncode,'stderr':proc.stderr[:1500],'data':info,'has_video':any(s.get('codec_type')=='video' for s in info.get('streams',[]))}
    except Exception as e: return {'id':wid,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: results=list(ex.map(probe,jobs))
pathlib.Path(__file__).with_name('videos.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('Vídeos inspeccionados:',len(results))
print('Con errores o sin pista de vídeo:',[r['id'] for r in results if r.get('error') or r.get('returncode') or not r.get('has_video')])
print('Con advertencias ffprobe:',[r['id'] for r in results if r.get('stderr')])
