const base=import.meta.env.VITE_API_BASE_URL||'/api';
export type History={role:'user'|'assistant';text:string};
export type Result={follow_up_question:string|null;care_type:string|null;urgency:string|null;red_flags:string[];reasoning:string;matched_caregivers:{caregiver_id:string;score:number;reason:string}[]};
export type Caregiver=Record<string,string>;
export type Booking={id:string;request_id:string;caregiver_id:string;caregiver_name:string;role:string;start:string;end:string;status:string;simulation:boolean};
export type Slot={start:string;end:string;available:boolean};
export type Handover={id:string;status:string;created?:string;summary:{reported_concern:string[];reported_flags:string[];language:string;location:{lat:number;lng:number}|null;duration:string;simulation:boolean}};
export type Hospital={id:string;name:string;url:string};
export type Lookup={id:string;status:string;result?:{contact?:string;address?:string;services?:string[];evidence?:string[];source_url?:string;hospital_name?:string;checked_at?:string;message?:string;disclaimer?:string}};
let token=localStorage.getItem('tg-session')||'';let pending:Promise<string>|null=null;
async function session(){if(token)return token;if(!pending)pending=fetch(base+'/session',{method:'POST'}).then(async r=>{if(!r.ok)throw Error('Could not start local session');const d=await r.json();token=d.token;localStorage.setItem('tg-session',token);return token;}).finally(()=>{pending=null;});return pending;}
export async function api<T>(path:string,body?:unknown,method?:string):Promise<T>{
 const key=await session();const r=await fetch(base+path,{method:method||(body?'POST':'GET'),headers:{'Content-Type':'application/json','X-Session-Token':key},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(20000)});
 if(!r.ok){if(r.status===401){token='';localStorage.removeItem('tg-session');}const e=await r.json().catch(()=>({}));throw Error(typeof e.detail==='string'?e.detail:`Request failed (${r.status}). Please retry.`);}return r.json();
}
export const caregivers=()=>api<Caregiver[]>('/caregivers');
export const triage=(body:unknown)=>api<{request_id:string;result:Result}>('/ui/triage',body);
