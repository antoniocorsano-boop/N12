#!/usr/bin/env python3
from __future__ import annotations

import cew_oa4_workbench_runtime as oa4_runtime

OA3_RUNTIME_MARKER = "CEW_OA3_RUNTIME_FIND_SIMILAR"


def augment(rendered: str, task: str) -> str:
    """Add explainable deterministic Find Similar to the existing OA panel.

    Results are review candidates only. OA-4 is chained into the same panel and
    consumes the exact session similarity run; no structural identity or canonical
    write is introduced here.
    """
    if OA3_RUNTIME_MARKER in rendered:
        return oa4_runtime.augment(rendered, task)

    style = '''
<style id="cew-oa3-runtime-style">
#oaSimilar{border-top:1px solid var(--line);margin-top:12px;padding-top:10px}.oa3-row{border:1px solid var(--line);border-radius:6px;padding:7px;margin:6px 0;background:#fff;font-size:12px}.oa3-score{font-size:16px;font-weight:850}.oa3-reasons{font-size:11px;color:var(--muted);overflow-wrap:anywhere}.oa3-strong{border-left:4px solid var(--ok)}.oa3-possible{border-left:4px solid var(--warn)}.oa3-weak{opacity:.76}
</style>'''
    rendered = rendered.replace('</head>', style + '</head>', 1)

    section = '''
<section id="oaSimilar" data-oa3-runtime="CEW_OA3_RUNTIME_FIND_SIMILAR">
  <h3>Trova simili</h3>
  <div class="oa-muted">Usa l'ultimo prototipo insegnato in questa sessione. Il risultato è solo una proposta di revisione.</div>
  <button id="oaFindSimilar" class="primary" type="button">Trova simili</button>
  <div id="oaSimilarResult"></div>
  <div class="authority-note">Nessun candidato viene confermato automaticamente. La revisione del gruppo appartiene a OA-4.</div>
</section>'''

    script = r'''
<script id="cew-oa3-runtime-script">
(() => {
const OA3_MARKER='CEW_OA3_RUNTIME_FIND_SIMILAR';
const WEIGHTS={GEOMETRY_KIND:.30,DIMENSION_RATIO:.20,ORIENTATION:.15,TOPOLOGY_HINT:.15,SPATIAL_CONTEXT:.10,ASSOCIATED_TEXT:.10};
const val=(o,...keys)=>{const p=o?.properties||{};for(const k of keys){if(o?.[k]!=null)return o[k];if(p[k]!=null)return p[k]}return null};
function lineFeatures(o){const g=o?.geometry||{};if(g.type!=='LINE'||!Array.isArray(g.a)||!Array.isArray(g.b))return null;const dx=Number(g.b[0])-Number(g.a[0]),dy=Number(g.b[1])-Number(g.a[1]);const length=Math.hypot(dx,dy);let angle=Math.atan2(dy,dx)*180/Math.PI;angle=((angle%180)+180)%180;return {length,angle}}
function tokens(v){if(!v)return new Set();return new Set(String(v).toUpperCase().replace(/×/g,'X').replace(/[,;:/()\[\]{}_\-]/g,' ').split(/\s+/).filter(Boolean))}
function signal(name,p,c){
 const pg=p?.geometry||{},cg=c?.geometry||{};
 if(name==='GEOMETRY_KIND'){const same=!!pg.type&&pg.type===cg.type;return [same?1:0,same?'GEOMETRY_KIND_MATCH':'GEOMETRY_KIND_MISMATCH']}
 if(name==='DIMENSION_RATIO'){const a=lineFeatures(p),b=lineFeatures(c);if(a&&b&&a.length>0&&b.length>0){const r=Math.min(a.length,b.length)/Math.max(a.length,b.length);return [r,'LENGTH_RATIO_'+r.toFixed(3)]}return [0,'DIMENSION_RATIO_UNAVAILABLE']}
 if(name==='ORIENTATION'){const a=lineFeatures(p),b=lineFeatures(c);if(a&&b){let d=Math.abs(a.angle-b.angle);d=Math.min(d,180-d);return [Math.max(0,1-d/90),'ORIENTATION_DELTA_'+d.toFixed(1)]}return [0,'ORIENTATION_UNAVAILABLE']}
 if(name==='TOPOLOGY_HINT'){const a=val(p,'topology_hint','connection_count'),b=val(c,'topology_hint','connection_count');if(a==null||b==null)return [0,'TOPOLOGY_UNAVAILABLE'];const same=String(a)===String(b);return [same?1:.25,same?'TOPOLOGY_MATCH':'TOPOLOGY_DIFFERENT']}
 if(name==='SPATIAL_CONTEXT'){const a=val(p,'spatial_context','context_role'),b=val(c,'spatial_context','context_role');if(a==null||b==null)return [0,'SPATIAL_CONTEXT_UNAVAILABLE'];const same=String(a).toUpperCase()===String(b).toUpperCase();return [same?1:0,same?'SPATIAL_CONTEXT_MATCH':'SPATIAL_CONTEXT_MISMATCH']}
 if(name==='ASSOCIATED_TEXT'){const a=tokens(val(p,'associated_text','text','label')),b=tokens(val(c,'associated_text','text','label'));if(!a.size||!b.size)return [0,'ASSOCIATED_TEXT_UNAVAILABLE'];const inter=[...a].filter(x=>b.has(x)).length,uni=new Set([...a,...b]).size,r=inter/uni;return [r,'ASSOCIATED_TEXT_JACCARD_'+r.toFixed(3)]}
 return [0,'UNKNOWN_SIGNAL'];
}
function latestPrototype(){const prefix='cew-oa2:'+TASK+':';const rows=[];for(let i=0;i<sessionStorage.length;i++){const k=sessionStorage.key(i);if(k&&k.startsWith(prefix)){try{const p=JSON.parse(sessionStorage.getItem(k));if(p?.state==='HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE')rows.push(p)}catch(e){}}}return rows.at(-1)||null}
function findSimilar(){const host=document.getElementById('oaSimilarResult'),proto=latestPrototype();if(!proto){host.innerHTML='<div class="oa2-error">Prima insegna un prototipo con “Questo è un…”.</div>';return}const source=scene?.source||{},ev=proto.source_evidence||{};for(const k of ['source_version_id','page_id','evidence_region_id','source_sha256']){if(source[k]!==ev[k]){host.innerHTML='<div class="oa2-error">Il prototipo appartiene a una diversa revisione/fonte. Ricrea il prototipo sulla scena corrente.</div>';return}}const anchor=(scene.objects||[]).find(o=>o.object_id===proto.anchor_object_id);if(!anchor){host.innerHTML='<div class="oa2-error">Oggetto prototipo non presente nella scena corrente.</div>';return}
 const rows=(scene.objects||[]).filter(o=>o.object_id!==anchor.object_id).map(c=>{let score=0;const reasons=[];for(const [name,w] of Object.entries(WEIGHTS)){const [s,r]=signal(name,anchor,c);score+=w*s;reasons.push(r)}score=Math.round(score*1e6)/1e6;const state=score>=.75?'STRONG_SIMILAR':score>=.50?'POSSIBLE_SIMILAR':score>0?'WEAK':'EXCLUDED';return {candidate_object_id:c.object_id,score,state,reason_codes:reasons,human_confirmation_required:true,object_type_created:false,family_membership_created:false,structural_identity_created:false,canonical_write_authorized:false}}).sort((a,b)=>b.score-a.score||String(a.candidate_object_id).localeCompare(String(b.candidate_object_id)));
 const run={state:'DETERMINISTIC_SIMILARITY_CANDIDATES',prototype_id:proto.prototype_id,object_type:proto.object_type,family_id:proto.family_id,weights:WEIGHTS,candidate_count:rows.length,candidates:rows,auto_confirm_cluster_authorized:false,structural_identity_created:false,canonical_write_authorized:false,engineering_authority_effect:'NONE',next_gate:'OA-4_CLUSTER_REVIEW'};sessionStorage.setItem('cew-oa3:'+TASK+':latest',JSON.stringify(run));
 host.innerHTML='<p class="oa-muted"><b>'+proto.family_label+'</b> · '+rows.length+' candidati · conferma umana richiesta</p>'+rows.map(r=>'<div class="oa3-row '+(r.state==='STRONG_SIMILAR'?'oa3-strong':r.state==='POSSIBLE_SIMILAR'?'oa3-possible':'oa3-weak')+'"><span class="oa3-score">'+Math.round(r.score*100)+'%</span> · <b>'+r.state+'</b><br>'+r.candidate_object_id+'<div class="oa3-reasons">'+r.reason_codes.join(' · ')+'</div></div>').join('');
}
function initOA3(){const teach=document.getElementById('oaTeach'),panel=document.getElementById('oaPanel');if(!panel||document.getElementById('oaSimilar'))return;(teach||panel).insertAdjacentHTML('afterend',OA3_SECTION);document.getElementById('oaFindSimilar').onclick=findSimilar;}
const OA3_SECTION=''' + repr(section) + r''';
let tries=0;const timer=setInterval(()=>{tries++;if(document.getElementById('oaPanel')&&typeof scene!=='undefined'&&scene){clearInterval(timer);initOA3()}else if(tries>80)clearInterval(timer)},100);
})();
</script>'''
    rendered = rendered.replace('</body>', script + '</body>', 1)
    return oa4_runtime.augment(rendered, task)
