from bootstrap import LOCK,download
if __name__=='__main__':
    for record in LOCK['archives']:
        if record.get('extract_to') in ['downloads/dotnet','windows/dotnet-sdk','downloads/jdk21']:download(record)

