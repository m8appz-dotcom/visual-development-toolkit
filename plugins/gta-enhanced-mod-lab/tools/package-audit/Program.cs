using CodeWalker.GameFiles;
using System.Text.Json;
using System.Security.Cryptography;

if(args.Length!=3)throw new ArgumentException("PackageAudit INPUT OUTPUT_JSON EXTRACTED_OUTPUT");
var root=Path.GetFullPath(args[0]);var report=Path.GetFullPath(args[1]);var output=Path.GetFullPath(args[2]);
if(Directory.Exists(output))throw new ArgumentException("Extraction output must be fresh");
Directory.CreateDirectory(output);
var rows=new List<object>();var archiveErrors=new List<object>();long extractedBytes=0;int count=0;
var allowed=new HashSet<string>{".ydr",".ydd",".yft",".ytd",".ymap",".ytyp",".ybn",".ymt",".meta",".xml",".ycd",".ypt",".yld",".lua"};
foreach(var p in Directory.EnumerateFiles(root,"*",SearchOption.AllDirectories).Where(p=>Path.GetExtension(p).Equals(".rpf",StringComparison.OrdinalIgnoreCase)).Order()){
 var rel=Path.GetRelativePath(root,p);var errors=new List<string>();
 try{
  var rpf=new RpfFile(p,rel);rpf.ScanStructure(_=>{},s=>errors.Add(s));
  if(errors.Count>0||rpf.AllEntries==null){archiveErrors.Add(new{archive=rel,errors});continue;}
  var packs=new List<RpfFile>();void Walk(RpfFile f){packs.Add(f);if(packs.Count>200)throw new Exception("Nested archive bound exceeded");foreach(var c in f.Children??new())Walk(c);}Walk(rpf);
  foreach(var pack in packs)foreach(var entry in pack.AllEntries.OfType<RpfFileEntry>()){
   var ext=Path.GetExtension(entry.Name).ToLowerInvariant();if(!allowed.Contains(ext))continue;
   if(++count>20000)throw new Exception("Resource count exceeds bound");
   string identity=rel+"::"+entry.Path;var notes=new List<string>();object? detail=null;string? outRel=null;int? version=null;int size=0;string? sha=null;
   try{
    if(entry.GetFileSize()>256_000_000)throw new Exception("Entry exceeds bound");
    var data=pack.ExtractFile(entry)??throw new Exception("Extraction returned no data");
    // CodeWalker returns decompressed resource payloads, not standalone RSC7 files.
    // Keep entry flags and verify the compression roundtrip before native readback.
    if(entry is RpfResourceFileEntry resource){
     var compressed=ResourceBuilder.Compress(data);
     if(!ResourceBuilder.Decompress(compressed).SequenceEqual(data))throw new Exception("Compression preservation failed");
     data=ResourceBuilder.AddResourceHeader(resource,compressed);
    }
    size=data.Length;extractedBytes+=size;
    if(extractedBytes>4_000_000_000)throw new Exception("Total extraction exceeds bound");
    if(data.Length>=8&&System.Text.Encoding.ASCII.GetString(data,0,4)=="RSC7")version=BitConverter.ToInt32(data,4);
    var parts=entry.Path.Replace('\\','/').Split('/');if(parts.Any(x=>x==".."||x.Contains(':'))||entry.Path.StartsWith('/'))throw new Exception("Unsafe entry path");
    outRel=Path.Combine(rel+".contents",Path.Combine(parts));var dest=Path.GetFullPath(Path.Combine(output,outRel));
    if(!dest.StartsWith(output+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new Exception("Path escaped output");
    Directory.CreateDirectory(Path.GetDirectoryName(dest)!);if(File.Exists(dest))throw new Exception("Duplicate extraction destination");File.WriteAllBytes(dest,data);
    sha=Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
    RpfManager.IsGen9=ext switch{".ydr" or ".ydd"=>version==159,".yft"=>version==171,".ytd"=>version==5,".ypt"=>version==71,_=>false};
    if(ext==".ymap"){
     var f=new YmapFile();f.Load(data);
     detail=new{entity_count=f.AllEntities?.Length??0,mlo_instances=f.MloEntities?.Length??0,entities=(f.AllEntities??Array.Empty<YmapEntityDef>()).Select(e=>new{archetype_hash=e._CEntityDef.archetypeName.Hash,parent=e._CEntityDef.parentIndex,lod_distance=e._CEntityDef.lodDist,position=new[]{e.Position.X,e.Position.Y,e.Position.Z}}).ToArray()};
    }else if(ext==".ytyp"){
     var f=new YtypFile();f.Load(data);
     detail=new{archetypes=(f.AllArchetypes??Array.Empty<Archetype>()).Select(a=>new{name_hash=a._BaseArchetypeDef.name.Hash,asset_hash=a._BaseArchetypeDef.assetName.Hash,texture_hash=a.TextureDict.Hash,physics_hash=a._BaseArchetypeDef.physicsDictionary.Hash,type=a.Type.ToString(),rooms=(a as MloArchetype)?.rooms?.Length,portals=(a as MloArchetype)?.portals?.Length,lod_distance=a.LodDist,bounds_min=new[]{a.BBMin.X,a.BBMin.Y,a.BBMin.Z},bounds_max=new[]{a.BBMax.X,a.BBMax.Y,a.BBMax.Z}}).ToArray()};
    }else if(ext==".ybn"){
     var f=new YbnFile();f.Load(data);if(f.Bounds==null)throw new Exception("Missing collision bounds");detail=new{type=f.Bounds.GetType().Name,collision_loaded=true};
    }
   }catch(Exception e){notes.Add(e.GetType().Name+": "+e.Message);}
   rows.Add(new{file=identity,extension=ext,bytes=size,sha256=sha,resource_version=version,extracted_path=outRel,errors=notes,detail});
  }
 }catch(Exception e){archiveErrors.Add(new{archive=rel,errors=new[]{e.GetType().Name+": "+e.Message}});}
}
Directory.CreateDirectory(Path.GetDirectoryName(report)!);
File.WriteAllText(report,JsonSerializer.Serialize(new{input=root,output,files=rows,archive_errors=archiveErrors,extracted_bytes=extractedBytes,gameplay_tested=false,encrypted_archives_not_bypassed=true},new JsonSerializerOptions{WriteIndented=true}));
Console.WriteLine(JsonSerializer.Serialize(new{resources=rows.Count,archive_errors=archiveErrors.Count,extracted_bytes=extractedBytes,report}));
