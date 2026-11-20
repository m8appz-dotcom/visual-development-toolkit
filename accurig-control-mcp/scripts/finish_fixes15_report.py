from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
job=read('data/jobs/b7bf311081164290bfc7461776b947ef.json')
q=read('reports/quality-b7bf311081164290bfc7461776b947ef.json')
review=read('reports/visual-b7bf311081164290bfc7461776b947ef.json')
close=read('reports/close-recovery-final.json')['data']['result']
offline=read('reports/fresh-offline-recovery-final.json')['data']['result']
source=Path(job['build_context']['model']['path'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==job['build_context']['model']['sha256']
assert review['verdict']=='requires_corrections' and q['deformation']=='failed'
assert close['exit_verified'] and close['preferences_restored']
assert offline['recovered']
result={
 'implementation_version':'0.3.0','tools':23,'fixes_implemented':15,
 'unit_tests':{'node':54,'python':2,'passed':True,'log':'reports/unit-v03-final.log'},
 'packaged_plugin_contract':'reports/plugin-contract.json',
 'pilot':{'original_input':str(source),'original_sha256':job['build_context']['model']['sha256'],
  'new_generation_id':job['id'],'from_scratch':True,'prior_failed_generation_reused':False,
  'preview_sha256':job['result']['preview']['sha256'],'structure':q['structure'],'deformation':q['deformation'],
  'motions':len(q['poses']),'progressive_samples':sum(len(p['samples']) for p in q['poses']),
  'visual':review['verdict'],'observed_poses':review['poses'],'open_defects':review['open_defects'],
  'accepted':False,'fbx_exported':False,'fbx_roundtrip_exercised':False,
  'export_limit':'Rejected candidate correctly blocked before native export; positive staging/FBX roundtrip not claimed for Nico.',
  'html':'http://x.tailb235ab.ts.net:18786/nico-fresh/?v=7'},
 'recovery':{'live_native_calculation_reconnected_without_replay':True,'automatic_receipt':job['build_context']['completion_receipt'],
  'completed_live_reconnect':'reports/reconnect-fresh-completed.json','offline_recovery':'reports/fresh-offline-recovery-final.json',
  'offline_export_blocked':'reports/fresh-offline-export-blocked.json'},
 'cleanup':close,'source_unchanged':True,'nico_zip_touched':False,
 'prior_generation_deletion':read('reports/deleted-16e56003518f4a57b8208d2150b91d39.json'),
 'rollback':'backups/fixes15-20261021',
 'next_step':'Nico rig is rejected. No retarget or Unreal performed. Retain exact rejected GLB for comparison, investigate native hand deformation before any new rig acceptance.'
}
(R/'reports/fixes15-final.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
p=R/'FIXES15-RESULTS.md';s=p.read_text(encoding='utf-8')
s=s.replace('46 testsNode y2 testsPython','54 testsNode y2 testsPython')
s=s.replace('El recibo real de Nico se comprobará al terminar.','Recibo automático real de Nico comprobado; reconexión durante cálculo, tras completar y recuperación offline sin regenerar verificadas.')
s=s.replace('comprobación nativa final pendiente mientras skin está activo.','Cierre real comprobado: salida nativa dejó un proceso residual; fallback sólo del PID propio revalidado, preferencias restauradas y verificadas. Se corrigió también la desconexión del inspector antes de esperar.')
s=s.replace('prueba nativa de Nico pendiente.','Exportación real de Nico bloqueada por revisión rechazada. No se ejecutó ni se atribuye un roundtrip FBX positivo a este candidato fallido.')
s+='''
## Resultado real del piloto

Importación nueva desde el FBX original,40 posiciones de dedos corregidas y verificadas antes de skin, generación nueva con100 articulaciones y216647 vértices ponderados,403606 triángulos. Estructura pasada;20 movimientos/60 muestras completados; deformación fallida en ambos puños. Codex observó frente, ambas manos, puños y hombros, y comparó mano derecha con referencia del FBX sin rig: hay pliegues y separaciones en el resultado nativo, incluso en reposo. Revisión detenida ante defectos; no se certifican otras vistas ni poses.

El MCP registró requires_corrections y bloqueó exportación. El piloto no es un rig aprobado. La implementación del controlador sí quedó probada, incluidos rechazos reales, recuperación de resultado y cierre. HTML conserva la referencia y la prueba nueva con textura original cargada; giro y zoom se verifican en el navegador. No se reparó el rig viejo ni se avanzó a Unreal.

El primer cierre mostró un proceso nativo residual después de destruir el contexto JavaScript; no basta desconectar el inspector. Se añadió salida acotada y terminación exclusivamente del PID propio después de revalidar ejecutable/fecha/lease y ausencia de build pendiente. Recuperación de cierre sólo tras terminar el controlador anterior. Pruebas y cierre real verificados; no se cerraron apps ajenas.

Informe completo: reports/fixes15-final.json. Artefacto rechazado conservado para revisión, fuentes y ZIP intactos.
'''
p.write_text(s,encoding='utf-8')
state='''
FINAL implementación0.3 completa,15 fixes+correcciones descubiertas.54Node+2Python passed; plugin independiente0.3/23tools instalado y contrato empaquetado real. Nico NUEVO b7bf311081164290bfc7461776b947ef desde SHA original,GLB c470acf650efe73ecf6e9d5a30bd86294a31fa285a51ea395cd070ae1607ba11.100joints216647v403606tris;20poses60samples,structurepassed,deformationfailedambospuños,visualrequires_corrections. No FBX final:export real bloqueada; no afirmar roundtrip positivo. Preview HTML /nico-fresh/?v=7 con originalsinrig y rechazado nuevo,originaltexturebyte intact, giro/zoom revisados; noZIP/noUnreal.

Recuperación activaR5→R6,completadaR6→R7 yofflineR9 verificadas sinreplay. Recibo automático fuente/actor/hashes. CierreR7 falló APPLICATION_EXIT_NOT_CONFIRMED: contextoJSdestruido/puertos cerrados peroPID35252nativo residual; cambiar ordenCDPnoes suficiente. Nuevo shutdown.mjs desconectaantesdeesperar y fallback sólo PID propio revalidado/lease/idle; recoveryclose opcional traspropietario muerto, bloqueabuildsinresolver. R9close recover_owned_session true comprobóPIDexacto, terminóresidual, verificóexit yrestaurópreferencias; session.jsonclosed_at. R9offline recuperacióncorrecta despuéscerrado,exportNOT_CONNECTED,close sin app correcto. Noapp35252restante. ClienteR9puedepararsecon__stop; reports/fixes15-final.json evidenciaactual. Próximo paso fuera deestaimplementación: investigar deformaciónnativamanos, noaprobar el rig existente.
'''
with (R/'FIXES15-STATE.md').open('a',encoding='utf-8') as f:f.write(state)
with (R/'STATUS.md').open('a',encoding='utf-8') as f:f.write(state)
print('Final report: implementation tested; Nico pilot explicitly rejected, export blocked; source and ZIP preserved.')
