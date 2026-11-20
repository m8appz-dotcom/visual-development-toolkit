"""Scoped source updates. Does not edit installed plugin caches or character assets."""
from pathlib import Path
import hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]
PIPE = Path('D:/visual-development-toolkit/kenneth-character-pipeline')
BLENDER = Path('D:/visual-development-toolkit/plugins/blender-agent')
BACKUP = ROOT/'backups/gemini-browser-20261024'

POLICY = '''# Revisión externa y encaje anatómico

La revisión externa obligatoria utiliza Gemini Flash, el más reciente disponible
en la cuenta autorizada **verificado en el selector al ejecutar**, exclusivamente
por navegador. No CLI, API, Auto ni sustitución silenciosa. La selección del usuario
prevalece. Si falta acceso, cuota, modelo o capacidad de adjuntos, registra pendiente
y bloquea la siguiente fase; no lo sustituyas por la autoevaluación de Codex.

Lee browser-access.md, gemini-browser.md y review-prompts.md locales antes de usar
el navegador. Abre conversación nueva para la revisión final independiente, conserva
cuenta y sesión. IAB primero; Chrome sólo ante límite comprobado. No envíes logs,
hashes, rutas, dictámenes previos ni defectos esperados al evaluador.

Prompt sencillo:

> Revisa este modelo 3D para detectar errores visuales de anatomía, proporciones, uniones y superficie. Indica dónde ves cada defecto y qué se observa. Si alguna zona no se puede evaluar, dilo.

Adjunta capturas reales sin procesar del modelo final en HTML: frente, ambos lados,
espalda, y ambas manos con muñeca y antebrazo visibles desde frente, perfil, palma y
dorso. No uses una mano aislada ni un cuerpo distante como prueba de su integración.
Una captura parcial sirve para rechazar un defecto; no para aprobar el cuerpo completo.
En animación adjunta el clip completo y revisa también las transiciones; una aprobación
estática no valida deformación. No envíes un enlace privado como si Gemini hubiera
podido abrirlo: verifica recepción real de los adjuntos y respuesta terminada.

Antes de unir piezas en Blender MCP, compara escala, ejes, longitud, sección y volumen
con el cuerpo. Mide varias secciones del antebrazo, muñeca y palma en la misma unidad;
registra ubicación, ancho, profundidad y cambios entre secciones. Un mínimo brusco,
intersección o salto de silueta debe investigarse; no impongas un umbral anatómico
universal ni apruebes por estar cerrada la malla. Conserva fuentes, cara y rollback.

Después del encaje, inspecciona las mismas vistas con luz neutra y compara el archivo
exportado y reimportado, no sólo Blender. Registra también límites del diagnóstico.
No declares automatizada esta medición si no se ejecutó sobre la geometría real.

Guarda respuesta original íntegra, conversación, cuenta verificada, selector de modelos,
capturas de navegador, archivos realmente enviados y sus hashes en el registro interno.
Los controles técnicos, el dictamen perceptivo y la aprobación del usuario son separados.
Gemini no reemplaza al usuario ni certifica topología o skinning. Cualquier defecto abierto,
zona requerida no observada, respuesta pendiente o archivo cambiado bloquea AccuRIG.
Un defecto corregido exige nueva revisión del resultado; no cambies su estado a resuelto
en el recibo viejo para habilitarlo. Toda aprobación debe corresponder al archivo exacto.

El control ejecutable es scripts/base_gate.py junto a external_review.py del pipeline
3d · Rig y movimiento y del controlador AccuRIG. No es una firma del proveedor ni puede
probar que un recibo escrito por el agente sea veraz: conserva las evidencias originales.
La ejecución general de Blender sigue permitiendo trabajo en progreso y diagnósticos;
la barrera se aplica a la aceptación y al paso a AccuRIG, no a guardar un borrador.

Si el usuario autoriza expresamente otro modelo de la familia Flash para esta revisión,
registra esa excepción para el archivo exacto; nunca conviertas una cuota en permiso
para cambiarlo automáticamente. `model_selection.user_authorization_path` referencia
un recibo user-model-choice/1 con source_sha256, selected, actor user, status authorized,
message_reference, authorization_text y evidence_path del mensaje real. Esta decisión
no aprueba el modelo 3D ni cambia el modelo predeterminado de las próximas tareas.
'''

def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        dest=BACKUP/'files'/path.relative_to(Path('D:/visual-development-toolkit'))
        if not dest.exists():
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    path.write_text(text,encoding='utf8')

for path in [PIPE/'skills/3d-preservation/references/external-visual-review.md',
             BLENDER/'skills/blender-agent/references/external-visual-review.md',
             ROOT/'skills/accurig-control/references/external-visual-review.md']:
    put(path,POLICY)

for path in [BLENDER/'skills/blender-agent/SKILL.md', ROOT/'skills/accurig-control/SKILL.md']:
    text=path.read_text(encoding='utf8')
    if '## Validación externa obligatoria' not in text:
        text+='\n## Validación externa obligatoria\n\nAntes de aceptar una adaptación anatómica o pasarla a AccuRIG aplica [revisión externa](references/external-visual-review.md): Gemini Flash más reciente disponible verificado, sólo navegador, prompt sencillo y evidencia real. Revisión pendiente, defectos abiertos o aprobación de usuario ausente bloquean el siguiente paso. No confundir malla cerrada con encaje correcto.\n'
    put(path,text)

p=BLENDER/'skills/blender-agent/references/visual-quality.md'
text=p.read_text(encoding='utf8')
if 'external-visual-review.md' not in text:
    text+='\nPara personajes y encajes anatómicos aplica además [validación externa obligatoria](external-visual-review.md), incluidas ambas muñecas con el antebrazo visible. No uses capturas de manos aisladas para aprobar la unión.\n'
put(p,text)

p=PIPE/'skills/3d-preservation/SKILL.md';text=p.read_text(encoding='utf8')
start=text.index('- Para revisión perceptiva')
end=text.index('\n- El agente técnico',start)
text=text[:start]+'- Para revisión perceptiva utiliza **Gemini Flash más reciente disponible verificado en navegador, exclusivamente navegador, sin CLI**, según [revisión externa](references/external-visual-review.md). Esta elección sustituye la antigua referencia fija a Argon. Si no está disponible, conserva el bloqueo y pregunta antes de sustituirlo. La revisión técnica no sustituye este tercero ni su dictamen reemplaza la aprobación del usuario.'+text[end:]
put(p,text)

for p in [PIPE/'skills/3d-preservation/references/base-model-filter.md',ROOT/'skills/accurig-control/references/base-model-filter.md']:
    text=p.read_text(encoding='utf8')
    text=text.split('\n## Recibo v2: tercero y usuario obligatorios')[0]
    text+='''
## Recibo v2: tercero y usuario obligatorios

Aplica [revisión externa](external-visual-review.md). Para pasar, el informe visual
incluye `external_review_path` y `user_approval_path`, rutas a JSON internos, nunca
texto de aprobación fabricado. Consulta `scripts/external_review.py` para el contrato.
El informe externo `gemini-browser-review/1` conserva provider Gemini, transport browser,
source_sha256, reviewer_id externo, account_verified, model_selection (selected,
available_flash_models, latest_available_verified), session_url real de conversación,
selector_evidence, response_evidence, prompt_path, raw_response_path, reviewed_images
(ruta:sha256), status, findings y limitations. No inventes nombres futuros de modelo.
`passed` requiere cero hallazgos y ninguna limitación de cobertura; hallazgos exigen una
nueva revisión, no marcar el informe anterior como resuelto. La aprobación del usuario
incluye source_sha256, actor user, status approved, message_reference, approval_text y
evidence_path. Guarda evidencias del mensaje real; el agente no puede concederla.

Se añade control técnico y visual `wrist_transition`. Evidencias obligatorias: front,
left, right, back, hands y left_wrist_front/profile/palm/back y right_wrist_front/profile/palm/back
(cada clave expandida individualmente), siempre con antebrazo visible. El reporte de
muñecas debe indicar mediciones realmente ejecutadas; una observación de malla cerrada
no aprueba anatomía. El controlador verifica recibo v2 y hashes antes de cargar/detectar/
generar. Los recibos v1 pasan a revisión pendiente; nunca se convierten solos a v2.
La ausencia del tercero no impide registrar un descarte temprano; sí impide un pase.
'''
    put(p,text)

for name in ['base_gate.py','external_review.py']:
    put(PIPE/'skills/3d-preservation/scripts'/name,(ROOT/'scripts'/name).read_text(encoding='utf8'))
    shutil.copyfile(ROOT/'scripts'/name,PIPE/'skills/3d-preservation/scripts'/name)

# Version only, preserve names, prompts, connections, audience and presentation.
for rel in ['plugin.json','.codex-plugin/plugin.json']:
    p=PIPE/rel;j=json.loads(p.read_text(encoding='utf8'));j['version']='0.3.4';put(p,json.dumps(j,ensure_ascii=False,indent=2)+'\n')

# The local marketplace reload, not this script, refreshes installed caches.
for f in (ROOT/'skills/accurig-control').rglob('*'):
    if f.is_file() and '__pycache__' not in str(f):
        put(Path('D:/visual-development-toolkit/plugins/accurig-control/skills/accurig-control')/f.relative_to(ROOT/'skills/accurig-control'),f.read_text(encoding='utf8'))

lock=ROOT/'runtime-lock.json';j=json.loads(lock.read_text())
for name in ['base_gate.py','external_review.py']:
    j['control_sources']['scripts/'+name]=hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest()
j['control_sources']['src/server.mjs']=hashlib.sha256((ROOT/'src/server.mjs').read_bytes()).hexdigest()
put(lock,json.dumps(j,indent=2)+'\n')

hashfile=BLENDER/'package-hashes.json';j=json.loads(hashfile.read_text())
for rel in ['skills/blender-agent/SKILL.md','skills/blender-agent/references/visual-quality.md','skills/blender-agent/references/external-visual-review.md']:
    j[rel]=hashlib.sha256((BLENDER/rel).read_bytes()).hexdigest()
put(hashfile,json.dumps(j,indent=2)+'\n')
print('Source policies and shared validation deployed; plugin caches untouched.')
