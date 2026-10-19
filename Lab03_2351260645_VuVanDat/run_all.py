"""One command: recompute experiments, capture log, rebuild the PDF report."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parent
(root/'results').mkdir(exist_ok=True)
with (root/'results/run.log').open('w',encoding='utf-8') as log:
    process=subprocess.Popen([sys.executable,'-u',str(root/'Lab03.py')],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
    for line in process.stdout:
        print(line,end='');log.write(line);log.flush()
    rc=process.wait()
if rc:raise SystemExit(rc)
subprocess.run([sys.executable,str(root/'build_report.py')],cwd=root,check=True)
