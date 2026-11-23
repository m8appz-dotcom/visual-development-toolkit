using AssetStudio;
using System.Text;
using System.Text.Json;
using System.Globalization;

CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
if(args.Length<2 || (args[0]!="inspect" && args[0]!="export")){Console.Error.WriteLine("Usage: AssetBridge inspect|export INPUT [OUTPUT] [TYPE]");return 2;}
try {
    var manager=new AssetsManager();
    Logger.Default=new QuietLogger();
    if(Directory.Exists(args[1])) manager.LoadFolder(args[1]); else manager.LoadFiles(args[1]);
    if(manager.assetsFileList.Count==0) throw new Exception("No supported Unity asset file was loaded.");
    var items=new List<object>();
    if(args[0]=="export" && args.Length<3)throw new Exception("Output folder is required.");
    var output=args.Length>2?Path.GetFullPath(args[2]):"";
    if(args[0]=="export")Directory.CreateDirectory(output);
    foreach(var file in manager.assetsFileList)foreach(var asset in file.Objects){
        var name=asset is NamedObject named?named.m_Name:asset.type.ToString();
        var type=asset.type.ToString(); string? saved=null; string? error=null;
        if(args[0]=="export" && (args.Length<4 || args[3]=="all" || args[3]==type)){
            var clean=new string(name.Select(c=>Path.GetInvalidFileNameChars().Contains(c)?'_':c).ToArray());
            var stem=Path.Combine(output,$"{Path.GetFileNameWithoutExtension(file.fileName)}_{asset.m_PathID}_{clean}");
            try {
                switch(asset){
                    case TextAsset text: saved=stem+".txt";File.WriteAllBytes(saved,text.m_Script);break;
                    case Texture2D texture: using(var data=texture.ConvertToStream(ImageFormat.Png,true)){if(data==null)throw new Exception("Texture decoding failed");saved=stem+".png";File.WriteAllBytes(saved,data.ToArray());}break;
                    case Sprite sprite: using(var image=sprite.GetImage()){if(image==null)throw new Exception("Sprite decoding failed");using var data=image.ConvertToStream(ImageFormat.Png);saved=stem+".png";File.WriteAllBytes(saved,data.ToArray());}break;
                    case AudioClip audio: var converter=new AudioClipConverter(audio);var bytes=converter.IsSupport?converter.ConvertToWav():audio.m_AudioData.GetData();if(bytes==null)throw new Exception("Audio decoding failed");saved=stem+(converter.IsSupport?".wav":converter.GetExtensionName());File.WriteAllBytes(saved,bytes);break;
                    case Mesh mesh: if(mesh.m_Vertices==null || mesh.m_VertexCount<=0)throw new Exception("Mesh has no vertices");var b=new StringBuilder();b.AppendLine("g "+clean);var stride=mesh.m_Vertices.Length/mesh.m_VertexCount;for(int i=0;i<mesh.m_VertexCount;i++)b.AppendLine($"v {-mesh.m_Vertices[i*stride]} {mesh.m_Vertices[i*stride+1]} {mesh.m_Vertices[i*stride+2]}");for(int i=0;i+2<mesh.m_Indices.Count;i+=3)b.AppendLine($"f {mesh.m_Indices[i+2]+1} {mesh.m_Indices[i+1]+1} {mesh.m_Indices[i]+1}");saved=stem+".obj";File.WriteAllText(saved,b.ToString());break;
                    case Font font: saved=stem+".font";File.WriteAllBytes(saved,font.m_FontData);break;
                    default: var dump=asset.Dump();if(dump==null)throw new Exception("No type tree is available for a readable dump; use the original GUI for supported specialized exports.");saved=stem+".txt";File.WriteAllText(saved,dump);break;
                }
            }catch(Exception ex){error=ex.Message;}
        }
        items.Add(new {file=file.fileName,path_id=asset.m_PathID,type,name,saved,error});
    }
    Console.WriteLine(JsonSerializer.Serialize(new {engine="AssetStudio 0.16.47",files=manager.assetsFileList.Count,items}));
    manager.Clear();return items.Count>0?0:3;
} catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}

class QuietLogger : ILogger {public void Log(LoggerEvent loggerEvent,string message){Console.Error.WriteLine($"[{loggerEvent}] {message}");}}
