import pathlib,struct
root=pathlib.Path(__file__).parent/'unity';root.mkdir(exist_ok=True)
payload=b'Modding Lab: original Unity TextAsset fixture. Damage=50.\n'
def i(value):return struct.pack('<i',value)
def aligned_string(text):
    blob=i(len(text))+text
    return blob+b'\0'*((-len(blob))%4)
data=aligned_string(b'LabReadme')+i(len(payload))+payload
meta=b'2018.4.36f1\0'+i(19)+b'\0'+i(1)+i(49)+b'\0'+struct.pack('<h',-1)+b'\0'*16+i(1)
meta+=b'\0'*((-(20+len(meta)))%4)
meta+=struct.pack('<qIII',1,0,len(data),0)+i(0)+i(0)+b'\0'
offset=256
header=struct.pack('>IIII',len(meta),offset+len(data),17,offset)+b'\0'*4
path=root/'lab.assets'
path.write_bytes(header+meta+b'\0'*(offset-len(header)-len(meta))+data)
(root/'expected.txt').write_bytes(payload)
print(path)
texture=aligned_string(b'LabRedTexture')+i(0)+b'\0'*4
texture+=i(4)+i(4)+i(8)+i(10)+i(1)+b'\1\0\0\0'
texture+=i(0)+i(1)+i(2)+i(0)+i(1)+struct.pack('<f',0)+i(1)+i(1)+i(1)+i(0)+i(0)+i(8)+struct.pack('<HHI',0xf800,0x07e0,0)
meta=b'2018.4.36f1\0'+i(19)+b'\0'+i(1)+i(28)+b'\0'+struct.pack('<h',-1)+b'\0'*16+i(1)
meta+=b'\0'*((-(20+len(meta)))%4)
meta+=struct.pack('<qIII',1,0,len(texture),0)+i(0)+i(0)+b'\0'
header=struct.pack('>IIII',len(meta),offset+len(texture),17,offset)+b'\0'*4
(root/'texture.assets').write_bytes(header+meta+b'\0'*(offset-len(header)-len(meta))+texture)
