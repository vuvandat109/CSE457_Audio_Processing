from pathlib import Path
import sys, json
sys.path.insert(0,str(Path(__file__).parent/'src'))
from lab2_pipeline import *
ROOT=Path(__file__).parent
acc,cm,results,_=evaluate(ROOT/'dataset',trim=True,add_delta=False)
results.to_csv(ROOT/'results.csv',index=False,encoding='utf-8-sig')
print('Accuracy =',acc)
print('Confusion matrix:')
print(cm)
print('\nTop-3 for test files:')
print(results.to_string(index=False))
for name,trim,delta in [('Baseline',True,False),('E1_no_endpoint',False,False),('E2_MFCC_delta',True,True)]:
    a,_,_,_=evaluate(ROOT/'dataset',trim=trim,add_delta=delta)
    print(f'{name}: {a*100:.1f}%')
