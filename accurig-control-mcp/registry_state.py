"""Back up/restore only AccuRIG window and recent-path preferences, never account data."""
import winreg,json,pathlib,sys
KEY=r'Software\Reallusion\ActorCore AccuRIG'
NAMES=('Width','Height','x','y','isMaximized','importModelPath','exportModelPath')
operation,filename=sys.argv[1:];filename=pathlib.Path(filename)
if operation=='backup':
 values={}
 try:
  with winreg.OpenKey(winreg.HKEY_CURRENT_USER,KEY) as key:
   for name in NAMES:
    try:value,kind=winreg.QueryValueEx(key,name);values[name]={'value':value,'kind':kind}
    except FileNotFoundError:values[name]=None
 except FileNotFoundError:values={name:None for name in NAMES}
 filename.write_text(json.dumps(values),encoding='utf8')
elif operation=='restore':
 values=json.loads(filename.read_text(encoding='utf8'));assert set(values)==set(NAMES)
 with winreg.CreateKey(winreg.HKEY_CURRENT_USER,KEY) as key:
  for name,value in values.items():
   if value is not None:winreg.SetValueEx(key,name,0,value['kind'],value['value'])
   else:
    try:winreg.DeleteValue(key,name)
    except FileNotFoundError:pass
else:raise ValueError('Unknown operation')
print(json.dumps({'operation':operation,'preference_count':len(NAMES)}))
