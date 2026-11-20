using CodeWalker.GameFiles;
using System.Security.Cryptography;
using System.Text.Json;

if(args.Length==1&&args[0]=="--self-test"){
 var selfTestResults=FragmentPreservation.SelfTest();Console.WriteLine(JsonSerializer.Serialize(selfTestResults));return;
}
if(args.Length!=4)throw new ArgumentException("RpfRebuild SOURCE_FOLDER CONVERTED_RESOURCES REPORT_JSON FRESH_OUTPUT");
var source=Path.GetFullPath(args[0]);var converted=Path.GetFullPath(args[1]);var report=Path.GetFullPath(args[2]);var output=Path.GetFullPath(args[3]);
if(Directory.Exists(output)||File.Exists(output))throw new ArgumentException("Output must be fresh");
if(source==converted||output.StartsWith(source+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase)||source.StartsWith(output+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new ArgumentException("Output must be separate from source");
var files=Directory.EnumerateFiles(source,"*",SearchOption.AllDirectories).ToArray();
if(files.Length>10000||files.Sum(f=>new FileInfo(f).Length)>3_000_000_000)throw new Exception("Input exceeds bound");
foreach(var f in files)if((File.GetAttributes(f)&FileAttributes.ReparsePoint)!=0)throw new Exception("Links rejected");
var hashes=files.ToDictionary(f=>f,f=>HashFile(f));
Directory.CreateDirectory(output);
var results=new List<object>();var used=new HashSet<string>(StringComparer.OrdinalIgnoreCase);var packs=0;
foreach(var file in files.Where(f=>Path.GetExtension(f).Equals(".rpf",StringComparison.OrdinalIgnoreCase))){
 var relative=Path.GetRelativePath(source,file);var destination=Path.GetFullPath(Path.Combine(output,relative));
 if(!destination.StartsWith(output+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new Exception("Output escaped");
 Directory.CreateDirectory(Path.GetDirectoryName(destination)!);File.Copy(file,destination,false);
 var archive=Scan(destination,relative);var before=Snapshot(archive);
 var descendants=Walk(archive).Reverse().ToArray();var changedParents=new HashSet<RpfFile>();var changes=new Dictionary<string,object>();var fragmentChecks=new List<object>();
 foreach(var pack in descendants){
  if(++packs>200)throw new Exception("Nested archive bound exceeded");
  var changed=changedParents.Contains(pack);
  foreach(var entry in pack.AllEntries.OfType<RpfResourceFileEntry>().OrderBy(e=>e.FileOffset).ToArray()){
   var extension=Path.GetExtension(entry.Name).ToLowerInvariant();
   int? expected=extension switch{ ".ydd" or ".ydr"=>159,".yft"=>171,".ytd"=>5,".ypt"=>71,_=>null};
   if(expected==null)continue;
   var path=Path.GetFullPath(Path.Combine(converted,relative+".contents",entry.Path));
   if(!path.StartsWith(converted+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new Exception("Converted path escaped");
   if(!File.Exists(path))throw new Exception("Missing converted resource: "+entry.Path);
   if(new FileInfo(path).Length>256_000_000)throw new Exception("Converted resource exceeds bound");
   var bytes=File.ReadAllBytes(path);
   if(bytes.Length<16||System.Text.Encoding.ASCII.GetString(bytes,0,4)!="RSC7"||BitConverter.ToInt32(bytes,4)!=expected)throw new Exception("Wrong converted version: "+entry.Path);
   var payload=ResourceBuilder.Decompress(bytes.Skip(16).ToArray());
   var hash=Hash(payload);var key=entry.Path;
   if(extension==".yft"){
    var originalPayload=pack.ExtractFile(entry);
    var originalBytes=ResourceBuilder.AddResourceHeader(entry,ResourceBuilder.Compress(originalPayload));
    (string fingerprint,int drawables,int physicsChildren,byte[] logical) oldFragment,newFragment;
    try{oldFragment=FragmentPreservation.Read(originalBytes);}catch(Exception e){throw new Exception("Source fragment "+entry.Path+" header version "+BitConverter.ToInt32(originalBytes,4),e);}
    try{newFragment=FragmentPreservation.Read(bytes);}catch(Exception e){throw new Exception("Converted fragment "+entry.Path+" header version "+BitConverter.ToInt32(bytes,4),e);}
    var comparison=FragmentPreservation.Compare(oldFragment.logical,newFragment.logical);
    if(!comparison.equivalent){
     File.WriteAllBytes(report+".fragment-source.json",oldFragment.logical);File.WriteAllBytes(report+".fragment-converted.json",newFragment.logical);
     throw new Exception("Fragment geometry/rig/collision preservation failed: "+entry.Path);
    }
    fragmentChecks.Add(new{file=key,source_signature=oldFragment.fingerprint,output_signature=newFragment.fingerprint,drawables=oldFragment.drawables,physics_children=oldFragment.physicsChildren,collision_requantization_max_delta=comparison.maxCollisionDelta,collision_coordinates_requantized=comparison.changedCollisionCoordinates,collision_tolerance="one per-axis quantum plus four float32 ULPs; topology/material metadata exact"});
   }
   RpfFile.CreateFile(entry.Parent,entry.Name,bytes,true);
   changes.Add(key,new{version=expected,sha256=hash});used.Add(path);changed=true;
  }
  if(changed){RpfFile.Defragment(pack,null,false);if(pack.Parent!=null)changedParents.Add(pack.Parent);}
 }
 var after=Snapshot(Scan(destination,relative));
 if(!before.Keys.Order().SequenceEqual(after.Keys.Order()))throw new Exception("Archive member set changed");
 var verified=new List<object>();
 foreach(var (key,old) in before){
  var next=after[key];
  if(changes.TryGetValue(key,out var change)){
   var expected=JsonSerializer.SerializeToElement(change);
   if(next.sha256!=expected.GetProperty("sha256").GetString()||next.version!=expected.GetProperty("version").GetInt32())throw new Exception("Converted payload readback mismatch: "+key);
  }else if(old.sha256!=next.sha256||old.version!=next.version)throw new Exception("Untouched member changed: "+key);
  verified.Add(new{file=key,converted=changes.ContainsKey(key),source=new{sha256=old.sha256,version=old.version},output=new{sha256=next.sha256,version=next.version}});
 }
 results.Add(new{source=file,output=destination,source_sha256=hashes[file],output_sha256=HashFile(destination),source_bytes=new FileInfo(file).Length,output_bytes=new FileInfo(destination).Length,converted_resources=changes.Count,members_verified=verified.Count,members=verified,fragment_preservation=fragmentChecks});
}
if(results.Count==0)throw new Exception("No RPF archive found");
var resourceFiles=Directory.EnumerateFiles(converted,"*",SearchOption.AllDirectories).Where(f=>new[]{".ydd",".ydr",".yft",".ytd",".ypt"}.Contains(Path.GetExtension(f).ToLowerInvariant())).Select(Path.GetFullPath).ToArray();
if(resourceFiles.Any(f=>!used.Contains(f)))throw new Exception("Orphan converted resources were not packed");
if(hashes.Any(kv=>HashFile(kv.Key)!=kv.Value))throw new Exception("Original input changed");
Directory.CreateDirectory(Path.GetDirectoryName(report)!);
File.WriteAllText(report,JsonSerializer.Serialize(new{archives=results,originals_preserved=true,converted_resources=used.Count,gameplay_tested=false,installation_performed=false},new JsonSerializerOptions{WriteIndented=true}));
Console.WriteLine(JsonSerializer.Serialize(new{archives=results.Count,converted_resources=used.Count,originals_preserved=true,report}));

static string Hash(byte[] data)=>Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
static string HashFile(string p){using var s=File.OpenRead(p);return Convert.ToHexString(SHA256.HashData(s)).ToLowerInvariant();}
static RpfFile Scan(string path,string relative){var messages=new List<string>();var f=new RpfFile(path,relative);f.ScanStructure(_=>{},e=>messages.Add(e));if(messages.Count>0||f.AllEntries==null)throw new Exception("RPF scan failed: "+string.Join(";",messages));return f;}
static IEnumerable<RpfFile> Walk(RpfFile f){yield return f;foreach(var c in f.Children??new())foreach(var nested in Walk(c))yield return nested;}
static Dictionary<string,(string sha256,int? version)> Snapshot(RpfFile root){
 var output=new Dictionary<string,(string sha256,int? version)>();long total=0;
 foreach(var pack in Walk(root))foreach(var e in pack.AllEntries.OfType<RpfFileEntry>()){
  if(e.Name.EndsWith(".rpf",StringComparison.OrdinalIgnoreCase))continue;
  if(e.GetFileSize()>256_000_000)throw new Exception("Entry exceeds bound");
  var bytes=pack.ExtractFile(e)??throw new Exception("Entry extraction failed");total+=bytes.Length;
  if(total>4_000_000_000||output.Count>=20000)throw new Exception("Snapshot exceeds bound");
  output.Add(e.Path,(Hash(bytes),(e as RpfResourceFileEntry)?.Version));
 }
 return output;
}
