from bootstrap import LOCK,download
if __name__=='__main__':
    for record in LOCK['archives']:
        if record.get('save_to')=='downloads/system-packages':download(record)

