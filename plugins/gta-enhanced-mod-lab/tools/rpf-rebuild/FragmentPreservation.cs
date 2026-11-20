using CodeWalker.GameFiles;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Xml.Linq;

// Compare logical geometry, rigs, collisions and physics children, independent
// of resource pointers, shader layout and archive compression.
static class FragmentPreservation {
 public static (string fingerprint,int drawables,int physicsChildren,byte[] logical) Read(byte[] bytes){
  RpfManager.IsGen9=BitConverter.ToInt32(bytes,4)==171;
  var file=new YftFile();file.Load(bytes);var f=file.Fragment??throw new Exception("Missing fragment");
  f.AssignChildrenSkeletonsAndBounds();
  var drawables=new List<object>();var physics=new List<object>();
  void Add(string path,FragDrawable? d){
   if(d==null)return;
   var models=new List<object>();
   foreach(var m in d.AllModels??Array.Empty<DrawableModel>()){
    var geometries=new List<object>();
    foreach(var g in m.Geometries??Array.Empty<DrawableGeometry>()){
     var vd=g.VertexData??g.VertexBuffer?.Data1??g.VertexBuffer?.Data2;
     using var positions=IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
     using var skin=IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
     using var triangles=IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
     foreach(var ix in g.IndexBuffer?.Indices??Array.Empty<ushort>())triangles.AppendData(BitConverter.GetBytes(ix));
     for(int i=0;i<(vd?.VertexCount??0);i++){
      uint flags=vd!.Info?.Flags??0;
      if((flags&1)!=0){var v=vd.GetVector3(i,0);positions.AppendData(BitConverter.GetBytes(v.X));positions.AppendData(BitConverter.GetBytes(v.Y));positions.AppendData(BitConverter.GetBytes(v.Z));}
      if((flags&6)==6){
       if(vd.Info!.GetComponentType(1) is not (VertexComponentType.Colour or VertexComponentType.UByte4)||vd.Info.GetComponentType(2) is not (VertexComponentType.Colour or VertexComponentType.UByte4))throw new Exception("Unsupported fragment skin layout");
       var w=vd.GetUByte4(i,1);var ix=vd.GetUByte4(i,2);skin.AppendData(new byte[]{w.R,w.G,w.B,w.A,ix.R,ix.G,ix.B,ix.A});
      }
     }
     geometries.Add(new{vertices=vd?.VertexCount??0,palette=g.BoneIds,positions=Convert.ToHexString(positions.GetHashAndReset()),weights_indices=Convert.ToHexString(skin.GetHashAndReset()),triangles=Convert.ToHexString(triangles.GetHashAndReset())});
    }
    models.Add(geometries);
   }
   var boneItems=d.Skeleton?.Bones?.Items??Array.Empty<Bone>();
   drawables.Add(new{path,bones=boneItems.Select(b=>new{b.Name,b.Index,b.ParentIndex,b.Tag,translation=new[]{b.Translation.X,b.Translation.Y,b.Translation.Z},rotation=new[]{b.Rotation.X,b.Rotation.Y,b.Rotation.Z,b.Rotation.W},scale=new[]{b.Scale.X,b.Scale.Y,b.Scale.Z}}).ToArray(),models,bounds=BoundsSignature(d.Bound)});
  }
  Add("main",f.Drawable);Add("cloth",f.DrawableCloth);
  var array=f.DrawableArray?.data_items??Array.Empty<FragDrawable>();for(int i=0;i<array.Length;i++)Add("array/"+i,array[i]);
  var group=f.PhysicsLODGroup;
  var lods=new[]{group?.PhysicsLOD1,group?.PhysicsLOD2,group?.PhysicsLOD3};int childCount=0;
  for(int l=0;l<lods.Length;l++){
   var lod=lods[l];if(lod==null)continue;
   var children=lod.Children?.data_items??Array.Empty<FragPhysTypeChild>();childCount+=children.Length;
   physics.Add(new{lod=l,archetype1=BoundsSignature(lod.Archetype1?.Bound),archetype2=BoundsSignature(lod.Archetype2?.Bound),children=children.Select(c=>new{c.BoneTag,c.GroupIndex,c.PristineMass,c.DamagedMass}).ToArray()});
   for(int i=0;i<children.Length;i++){Add($"physics/{l}/{i}/1",children[i]?.Drawable1);Add($"physics/{l}/{i}/2",children[i]?.Drawable2);}
  }
  var transforms=f.BoneTransforms?.Items;
  var transformsHash=transforms==null?null:Convert.ToHexString(SHA256.HashData(System.Runtime.InteropServices.MemoryMarshal.AsBytes(transforms.AsSpan())));
  var logical=JsonSerializer.SerializeToUtf8Bytes(new{drawables,physics,transformsHash});
  return (Convert.ToHexString(SHA256.HashData(logical)).ToLowerInvariant(),drawables.Count,childCount,logical);
 }
 static object? BoundsSignature(Bounds? b){
  if(b==null)return null;
  var sb=new StringBuilder();Bounds.WriteXmlNode(b,sb,0);var xml=XElement.Parse(sb.ToString());
  // CodeWalker requantizes collision vertices when saving (CalculateQuantum and
  // BuildVertices). Preserve topology/materials exactly and compare decoded
  // positions against their own signed-16-bit quantum, not a blanket tolerance.
  foreach(var vertices in xml.Descendants("Vertices").ToArray())vertices.Remove();
  var geometry=new List<object>();
  void Walk(Bounds bound){
   if(bound is BoundGeometry g){var saved=(g.BoxMax-g.BoxMin)*0.5f/32767.0f;geometry.Add(new{quantum=new[]{g.Quantum.X,g.Quantum.Y,g.Quantum.Z},expected_saved_quantum=new[]{saved.X,saved.Y,saved.Z},vertices=g.Vertices?.Select(v=>new[]{v.X,v.Y,v.Z}).ToArray(),shrunk=g.VerticesShrunk?.Select(v=>new[]{v.X,v.Y,v.Z}).ToArray()});}
   if(bound is BoundComposite composite)foreach(var child in composite.Children?.data_items??Array.Empty<Bounds>())if(child!=null)Walk(child);
  }
  Walk(b);return new{metadata_xml=xml.ToString(SaveOptions.DisableFormatting),geometry_records=geometry};
 }
 public static (bool equivalent,double maxCollisionDelta,int changedCollisionCoordinates) Compare(byte[] before,byte[] after){
  var a=JsonNode.Parse(before);var b=JsonNode.Parse(after);double maximum=0;int changed=0;
  bool Visit(JsonNode? x,JsonNode? y){
   if(x==null||y==null)return x==null&&y==null;
   if(JsonNode.DeepEquals(x,y))return true;
   if(x is JsonObject xo&&y is JsonObject yo){
    if(xo.ContainsKey("geometry_records")){
     if(xo["metadata_xml"]!.GetValue<string>()!=yo["metadata_xml"]!.GetValue<string>())return false;
     var old=xo["geometry_records"]!.AsArray();var next=yo["geometry_records"]!.AsArray();if(old.Count!=next.Count)return false;
     for(int i=0;i<old.Count;i++){
      var oq=old[i]!["quantum"]!.AsArray();var nq=next[i]!["quantum"]!.AsArray();
      var expected=old[i]!["expected_saved_quantum"]!.AsArray();
      for(int axis=0;axis<3;axis++){
       var actual=nq[axis]!.GetValue<double>();var saved=expected[axis]!.GetValue<double>();
       var epsilon=4.0*Math.Abs(MathF.BitIncrement((float)Math.Abs(saved))-(float)Math.Abs(saved));
       if(!double.IsFinite(actual)||actual<0||!double.IsFinite(saved)||Math.Abs(actual-saved)>epsilon)return false;
      }
      foreach(var kind in new[]{"vertices","shrunk"}){
       var ov=old[i]![kind];var nv=next[i]![kind];if(ov==null||nv==null){if(ov!=null||nv!=null)return false;continue;}
       var ol=ov.AsArray();var nl=nv.AsArray();if(ol.Count!=nl.Count)return false;
       for(int v=0;v<ol.Count;v++)for(int axis=0;axis<3;axis++){
        var from=ol[v]![axis]!.GetValue<double>();var to=nl[v]![axis]!.GetValue<double>();
        var quantum=Math.Max(Math.Abs(oq[axis]!.GetValue<double>()),Math.Abs(nq[axis]!.GetValue<double>()));
        var magnitude=(float)Math.Max(Math.Abs(from),Math.Abs(to));var rounding=4.0*Math.Abs(MathF.BitIncrement(magnitude)-magnitude);
        var delta=Math.Abs(from-to);if(!double.IsFinite(delta)||!double.IsFinite(quantum)||delta>quantum+rounding)return false;
        if(delta>0){changed++;maximum=Math.Max(maximum,delta);}
       }
      }
     }
     return true;
    }
    if(!xo.Select(kv=>kv.Key).Order().SequenceEqual(yo.Select(kv=>kv.Key).Order()))return false;
    return xo.All(kv=>Visit(kv.Value,yo[kv.Key]));
   }
   if(x is JsonArray xa&&y is JsonArray ya)return xa.Count==ya.Count&&xa.Select((node,i)=>Visit(node,ya[i])).All(v=>v);
   return JsonNode.DeepEquals(x,y);
  }
  return (Visit(a,b),maximum,changed);
 }
 public static object SelfTest(){
  byte[] Example(double position,string material="same",string mesh="same",int bone=4,double quantum=0.01)=>JsonSerializer.SerializeToUtf8Bytes(new{mesh,bone,bounds=new{metadata_xml=material,geometry_records=new[]{new{quantum=new[]{quantum,quantum,quantum},expected_saved_quantum=new[]{0.01,0.01,0.01},vertices=new[]{new[]{position,0.0,0.0}},shrunk=(double[][]?)null}}}});
  var original=Example(1.0);
  if(!Compare(original,Example(1.005)).equivalent)throw new Exception("Valid collision quantum was rejected");
  if(Compare(original,Example(1.02)).equivalent)throw new Exception("Collision beyond quantum was accepted");
  if(Compare(original,Example(1.0,material:"different material/topology")).equivalent)throw new Exception("Collision metadata change was accepted");
  if(Compare(original,Example(1.0,mesh:"different mesh/skin")).equivalent)throw new Exception("Mesh change was accepted");
  if(Compare(original,Example(1.0,bone:7)).equivalent)throw new Exception("Bone/physics change was accepted");
  if(Compare(original,Example(1.5,quantum:1.0)).equivalent)throw new Exception("Inflated collision quantum was accepted");
  return new{status="passed",quantized_coordinate_case=true,rejected_cases=5};
 }
}
