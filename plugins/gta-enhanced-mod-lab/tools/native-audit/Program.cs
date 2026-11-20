using CodeWalker.GameFiles;
using CodeWalker.Core.Utils;
using System.Text.Json;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;

if(args.Length==3&&args[0]=="--make-negative-fixtures"){
 var source=File.ReadAllBytes(args[1]);var target=Path.GetFullPath(args[2]);Directory.CreateDirectory(target);
 foreach(var kind in new[]{"zero-weights","bad-skin-index","bad-triangle-index"}){
  RpfManager.IsGen9=BitConverter.ToInt32(source,4)==159;var f=new YddFile();f.Load(source);
  var g=f.Drawables.SelectMany(d=>d.AllModels).SelectMany(m=>m.Geometries).First(g=>g.VertexData?.Info!=null&&(g.VertexData.Info.Flags&6)==6);
  if(kind=="zero-weights")g.VertexData.SetUByte4(0,1,new SharpDX.Color(0,0,0,0));
  if(kind=="bad-skin-index"){g.VertexData.SetUByte4(0,1,new SharpDX.Color(255,0,0,0));g.VertexData.SetUByte4(0,2,new SharpDX.Color(255,0,0,0));}
  if(kind=="bad-triangle-index")g.IndexBuffer.Indices[0]=ushort.MaxValue;
  File.WriteAllBytes(Path.Combine(target,kind+".ydd"),f.Save());
 }
 Console.WriteLine("Created three negative fixtures from an isolated copy; never install these files.");return;
}
if(args.Length<2)throw new ArgumentException("NativeAudit INPUT REPORT [CONVERTED_OUTPUT]");
var root=Path.GetFullPath(args[0]);var rows=new List<object>();var converted=new List<object>();
var targets=new HashSet<string>{".ydd",".yft",".ydr",".ytd",".ymt",".yld",".ycd",".ypt",".dll",".asi",".endll",".ndll"};
foreach(var p in Directory.EnumerateFiles(root,"*",SearchOption.AllDirectories).Order()){
 var ext=Path.GetExtension(p).ToLowerInvariant();if(!targets.Contains(ext))continue;
 var bytes=File.ReadAllBytes(p);var rel=Path.GetRelativePath(root,p);var errors=new List<string>();var warnings=new List<string>();object? detail=null;
 int? version=bytes.Length>=8&&System.Text.Encoding.ASCII.GetString(bytes,0,4)=="RSC7"?BitConverter.ToInt32(bytes,4):null;
 bool gen9=ext switch{".ydd" or ".ydr"=>version==159,".yft"=>version==171,".ytd"=>version==5,".ypt"=>version==71,_=>false};
 try{
  RpfManager.IsGen9=gen9;
  if(ext==".ydd") {var f=new YddFile();f.Load(bytes);detail=AuditDrawables(f.Drawables??Array.Empty<Drawable>(),errors,warnings,File.Exists(Path.ChangeExtension(p,".yld")));}
  else if(ext==".yft") {var f=new YftFile();f.Load(bytes);if(f.Fragment?.Drawable==null)errors.Add("Missing fragment drawable");else detail=AuditDrawables(new[]{f.Fragment.Drawable},errors,warnings);}
  else if(ext==".ydr") {var f=new YdrFile();f.Load(bytes);if(f.Drawable==null)errors.Add("Missing drawable");else detail=AuditDrawables(new[]{f.Drawable},errors,warnings);}
  else if(ext==".ytd") {
   var f=LoadYtdComplete(bytes,warnings);var textures=f.TextureDict?.Textures?.data_items??Array.Empty<Texture>();
   foreach(var t in textures){if(t.Width==0||t.Height==0)errors.Add("Zero texture size: "+t.Name);if(t.Levels==0)errors.Add("Missing texture levels: "+t.Name);if(t.Width>=4096||t.Height>=4096)warnings.Add("Large texture, profile VRAM: "+t.Name);if(t.Levels==1)warnings.Add("Single mip level: "+t.Name);}
   detail=new{texture_count=textures.Length,textures=textures.Select(t=>new{t.Name,t.Width,t.Height,t.Levels,format=t.Format.ToString(),gen9_format=t.G9_Format.ToString(),data_sha256=t.Data?.FullData==null?null:Convert.ToHexString(SHA256.HashData(t.Data.FullData)).ToLowerInvariant()}).ToArray()};
  }
  else if(ext==".ymt") {var f=new YmtFile();if(version!=null)f.Load(bytes);else f.Load(bytes,new RpfBinaryFileEntry{Name=Path.GetFileName(p)});detail=new{format=f.Pso!=null?"PSO":f.Rbf!=null?"RBF":f.FileFormat.ToString(),has_meta=f.Meta!=null,has_pso=f.Pso!=null,has_rbf=f.Rbf!=null};if(f.Meta==null&&f.Pso==null&&f.Rbf==null)errors.Add("No recognized metadata payload");}
  else if(ext==".yld") {var f=new YldFile();RpfFile.LoadResourceFile(f,bytes,8);detail=new{cloth_entries=f.Dict?.Count??0,requires_cloth_runtime_test=true};if(f.LoadException!=null)errors.Add(f.LoadException);if(f.ClothDictionary==null)errors.Add("Missing cloth dictionary");}
  else if(ext==".ycd") {var f=new YcdFile();RpfFile.LoadResourceFile(f,bytes,46);f.InitDictionaries();var animations=f.AnimMap.Values.Select(a=>a.Animation).Where(a=>a!=null).ToArray();foreach(var a in animations)if(!float.IsFinite(a.Duration)||a.Duration<0)errors.Add("Invalid animation duration");detail=new{clips=f.ClipMap.Count,animations=animations.Select(a=>new{duration=a.Duration,bone_tracks=a.BoneIds?.data_items?.Length??0}).ToArray(),pose_binding_tested=false};}
  else if(ext==".ypt") {var f=new YptFile();f.Load(bytes);detail=new{effects=f.AllEffects?.Length??0,drawables=f.DrawableDict?.Count??0};if(f.PtfxList==null)errors.Add("Missing particle effects list");}
  else {
   using var pe=new PEReader(new MemoryStream(bytes));
   if(pe.HasMetadata){var m=pe.GetMetadataReader();var assembly=m.GetAssemblyDefinition();detail=new{managed=true,name=m.GetString(assembly.Name),version=assembly.Version.ToString(),references=m.AssemblyReferences.Select(h=>m.GetAssemblyReference(h)).Select(a=>new{name=m.GetString(a.Name),version=a.Version.ToString()}).ToArray(),api_names=m.TypeReferences.Select(h=>m.GetTypeReference(h)).Select(t=>m.GetString(t.Namespace)+"."+m.GetString(t.Name)).Where(n=>n.StartsWith("GTA.")||n.Contains("Memory")||n.Contains("Hook")).Distinct().Take(80).ToArray()};}
   else detail=new{managed=false,machine=pe.PEHeaders.CoffHeader.Machine.ToString()};
  }
 }catch(Exception ex){errors.Add(ex.GetType().Name+": "+ex.Message);}
 bool convertible=ext is ".ydd" or ".ydr" or ".yft" or ".ytd" or ".ypt";
 if(convertible&&!gen9)warnings.Add("Gen8 input: conversion required for Enhanced");
 rows.Add(new{file=rel,bytes=bytes.Length,sha256=Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant(),resource_version=version,is_gen9=convertible?(bool?)gen9:null,parsed=detail!=null,errors,warnings,detail});
 if(args.Length>=3&&convertible&&errors.Count==0){
  var logs=new List<string>();var target=Path.Combine(Path.GetFullPath(args[2]),rel);
  if(Path.GetFullPath(target)==p)throw new Exception("Conversion must preserve input");
  try{
   byte[] output;bool changed;
   if(ext==".ytd"&&!gen9){RpfManager.IsGen9=false;var fixedYtd=LoadYtdComplete(bytes,logs);RpfManager.IsGen9=true;output=fixedYtd.Save();changed=true;logs.Add("Converted YTD with full block-compressed mip payload recovered from original resource");}
   else{RpfManager.IsGen9=true;output=Gen9Converter.TryConvert(bytes,ext,s=>logs.Add(s),rel,true,out changed);}
   if(output==null)throw new Exception("Converter returned null");Directory.CreateDirectory(Path.GetDirectoryName(target)!);File.WriteAllBytes(target,output);converted.Add(new{file=rel,changed,bytes=output.Length,version=BitConverter.ToInt32(output,4),sha256=Convert.ToHexString(SHA256.HashData(output)).ToLowerInvariant(),logs});
  }
  catch(Exception e){converted.Add(new{file=rel,error=e.Message,logs});}
 }
}
Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(args[1]))!);
File.WriteAllText(args[1],JsonSerializer.Serialize(new{files=rows,converted,gameplay_tested=false,visual_deformation_tested=false},new JsonSerializerOptions{WriteIndented=true}));
Console.WriteLine($"Audited {rows.Count} files; report: {args[1]}");

static YtdFile LoadYtdComplete(byte[] bytes,List<string> notes){
 var f=new YtdFile();f.Load(bytes);
 if(bytes.Length<16||BitConverter.ToInt32(bytes,4)!=13)return f;
 var compressed=bytes.ToArray();var entry=RpfFile.CreateResourceFileEntry(ref compressed,13);
 var resource=ResourceBuilder.Decompress(compressed);
 var reader=new ResourceDataReader(entry,resource){IsGen9=false};
 foreach(var texture in f.TextureDict?.Textures?.data_items??Array.Empty<Texture>()){
  int expected=texture.CalcDataSize();int loaded=texture.Data?.FullData?.Length??0;
  if(expected==loaded)continue;
  if(expected<=0||expected>512*1024*1024)throw new Exception("Unexpected texture payload size: "+texture.Name);
  var complete=reader.ReadBytesAt(texture.DataPointer,(uint)expected,false);
  if(complete.Length!=expected)throw new Exception("Incomplete mip payload: "+texture.Name);
  if(texture.Data==null)throw new Exception("Missing texture data block: "+texture.Name);
  texture.Data.FullData=complete;
  notes.Add($"Legacy decoder read {loaded} bytes; recovered complete {expected}-byte mip payload from original resource for {texture.Name}");
 }
 return f;
}

static object AuditDrawables(IEnumerable<DrawableBase> drawables,List<string> errors,List<string> warnings,bool hasCloth=false){
 var drawableArray=drawables.ToArray();var inherited=drawableArray.Select(d=>d.Skeleton?.Bones?.Items).FirstOrDefault(b=>b?.Length>0);
 var results=new List<object>();
 foreach(var d in drawableArray){
  var ownBones=d.Skeleton?.Bones?.Items??Array.Empty<Bone>();var bones=ownBones.Length>0?ownBones:inherited??Array.Empty<Bone>();var models=d.AllModels??Array.Empty<DrawableModel>();
  foreach(var b in bones){
   if(b.ParentIndex<-1||b.ParentIndex>=bones.Length)errors.Add("Invalid parent: "+b.Name);
   var values=new[]{b.Translation.X,b.Translation.Y,b.Translation.Z,b.Rotation.X,b.Rotation.Y,b.Rotation.Z,b.Rotation.W,b.Scale.X,b.Scale.Y,b.Scale.Z};
   if(values.Any(v=>!float.IsFinite(v)))errors.Add("Non-finite bind transform: "+b.Name);
   if(Math.Abs(b.Scale.X*b.Scale.Y*b.Scale.Z)<1e-9)errors.Add("Singular scale: "+b.Name);
   var seen=new HashSet<int>();int i=b.Index;
   while(i>=0&&i<bones.Length){if(!seen.Add(i)){errors.Add("Bone hierarchy cycle: "+b.Name);break;}i=bones[i].ParentIndex;}
  }
  var duplicateTags=bones.GroupBy(b=>b.Tag).Where(g=>g.Count()>1).Select(g=>g.Key).ToArray();if(duplicateTags.Length>0)warnings.Add("Duplicate bone tags; review animation mapping");
  int vertexCount=0,skinnedVertices=0,zeroWeights=0,badWeightSums=0,badBlendIndices=0,badBonePalette=0,badTriangleIndices=0,nonfinitePositions=0;
  using var skinHash=IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
  var geoms=models.SelectMany(m=>m.Geometries??Array.Empty<DrawableGeometry>()).ToArray();
  int clothReviewVertices=0;
  foreach(var g in geoms){
   var vd=g.VertexData??g.VertexBuffer?.Data1??g.VertexBuffer?.Data2;if(vd==null)continue;vertexCount+=vd.VertexCount;
   badTriangleIndices+=(g.IndexBuffer?.Indices??Array.Empty<ushort>()).Count(i=>i>=vd.VertexCount);
   bool clothCandidate=hasCloth&&(ownBones.Length==0||g.BoneIds?.Any(i=>i>=bones.Length)==true);
   if(clothCandidate){clothReviewVertices+=vd.VertexCount;continue;}
   foreach(var id in g.BoneIds??Array.Empty<ushort>())skinHash.AppendData(BitConverter.GetBytes(id));
   if(g.BoneIds!=null&&bones.Length>0)badBonePalette+=g.BoneIds.Count(i=>i>=bones.Length);
   uint flags=vd.Info?.Flags??0;
   for(int v=0;v<vd.VertexCount;v++){
    if((flags&1)!=0){var pos=vd.GetVector3(v,0);if(!float.IsFinite(pos.X)||!float.IsFinite(pos.Y)||!float.IsFinite(pos.Z))nonfinitePositions++;}
    if((flags&6)!=6)continue;
    var weightType=vd.Info!.GetComponentType(1);var indexType=vd.Info.GetComponentType(2);
    if(weightType is not (VertexComponentType.Colour or VertexComponentType.UByte4)||indexType is not (VertexComponentType.Colour or VertexComponentType.UByte4)){warnings.Add("Unsupported skin vertex layout: "+weightType+"/"+indexType);break;}
    skinnedVertices++;var w=vd.GetUByte4(v,1);var ix=vd.GetUByte4(v,2);int[] ws={w.R,w.G,w.B,w.A},ids={ix.R,ix.G,ix.B,ix.A};int sum=ws.Sum();
    skinHash.AppendData(new byte[]{w.R,w.G,w.B,w.A,ix.R,ix.G,ix.B,ix.A});
    if(sum==0)zeroWeights++;else if(Math.Abs(sum-255)>2)badWeightSums++;
    int count=g.BoneIds?.Length>0?g.BoneIds.Length:bones.Length;
    for(int j=0;j<4;j++)if(ws[j]>0&&(count==0||ids[j]>=count))badBlendIndices++;
   }
  }
  if(zeroWeights>0)errors.Add($"Unweighted skinned vertices: {zeroWeights}");if(badBlendIndices>0)errors.Add($"Skin indices outside bone palette: {badBlendIndices}");if(badBonePalette>0)errors.Add($"Bone palette outside skeleton: {badBonePalette}");if(badTriangleIndices>0)errors.Add($"Triangle indices out of bounds: {badTriangleIndices}");if(nonfinitePositions>0)errors.Add($"Non-finite vertices: {nonfinitePositions}");if(badWeightSums>0)warnings.Add($"Weight sums outside quantization tolerance: {badWeightSums}");
  if(d.DrawableModels?.High==null)warnings.Add("No high LOD; verify intended drawable type");
  if(clothReviewVertices>0)warnings.Add($"Cloth/child components require YLD mapping and pose review: {clothReviewVertices} vertices; ordinary skin-index rules were not applied");
  results.Add(new{bones=ownBones.Length,resolved_bones=bones.Length,cloth_review_vertices=clothReviewVertices,skinning_sha256=Convert.ToHexString(skinHash.GetHashAndReset()).ToLowerInvariant(),duplicate_bone_tags=duplicateTags,geometry_count=geoms.Length,vertex_count=vertexCount,skinned_vertices=skinnedVertices,zero_weights=zeroWeights,bad_weight_sums=badWeightSums,bad_blend_indices=badBlendIndices,bad_bone_palette=badBonePalette,bad_triangle_indices=badTriangleIndices,nonfinite_positions=nonfinitePositions,lod_models=new{high=d.DrawableModels?.High?.Length??0,medium=d.DrawableModels?.Med?.Length??0,low=d.DrawableModels?.Low?.Length??0,very_low=d.DrawableModels?.VLow?.Length??0},bone_signature=bones.Select(b=>new{b.Name,b.Index,b.ParentIndex,b.Tag,translation=new[]{b.Translation.X,b.Translation.Y,b.Translation.Z},rotation=new[]{b.Rotation.X,b.Rotation.Y,b.Rotation.Z,b.Rotation.W},scale=new[]{b.Scale.X,b.Scale.Y,b.Scale.Z}}).ToArray()});
 }
 return results;
}
