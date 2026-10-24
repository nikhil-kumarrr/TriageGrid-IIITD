const base=import.meta.env.VITE_API_BASE_URL||'/api';
export type History={role:'user'|'assistant';text:string};
export type Result={follow_up_question:string|null;care_type:string|null;urgency:string|null;red_flags:string[];reasoning:string;matched_caregivers:{caregiver_id:string;score:number;reason:string}[]};
export type Caregiver=Record<string,string>;
export type Booking={id:string;request_id:string;caregiver_id:string;caregiver_name:string;role:string;start:string;end:string;status:string;simulation:boolean};
export type Slot={start:string;end:string;available:boolean};
export type Handover={id:string;status:string;created?:string;summary:{reported_concern:string[];reported_flags:string[];language:string;location:{lat:number;lng:number}|null;duration:string;simulation:boolean}};
export type Hospital={id:string;name:string;url:string};
export type Lookup={id:string;status:string;result?:{contact?:string;address?:string;services?:string[];evidence?:string[];source_url?:string;hospital_name?:string;checked_at?:string;message?:string;disclaimer?:string}};
export type AuthUser={name:string;email:string;phone?:string};
let token=localStorage.getItem('tg-session')||'';let pending:Promise<string>|null=null;
export function setSessionToken(t:string){token=t;localStorage.setItem('tg-session',t);}
export function clearSessionToken(){token='';localStorage.removeItem('tg-session');}
async function session(force=false){if(token&&!force)return token;if(!pending)pending=fetch(base+'/session',{method:'POST'}).then(async r=>{if(!r.ok)throw Error('Could not start local session');const d=await r.json();token=d.token;localStorage.setItem('tg-session',token);return token;}).finally(()=>{pending=null;});return pending;}
export async function api<T>(path:string,body?:unknown,method?:string):Promise<T>{
 let key=await session();let r=await fetch(base+path,{method:method||(body?'POST':'GET'),headers:{'Content-Type':'application/json','X-Session-Token':key},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(20000)});
 if(!r.ok&&r.status===401){
  clearSessionToken();
  try{
   key=await session(true);
   r=await fetch(base+path,{method:method||(body?'POST':'GET'),headers:{'Content-Type':'application/json','X-Session-Token':key},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(20000)});
  }catch{}
 }
 if(!r.ok){const e=await r.json().catch(()=>({}));throw Error(typeof e.detail==='string'?e.detail:`Request failed (${r.status}). Please retry.`);}return r.json();
}
export async function loginApi(email:string,password:string):Promise<{success:boolean;user:AuthUser;token:string}>{
 const r=await fetch(base+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
 const data=await r.json().catch(()=>({}));
 if(!r.ok)throw Error(typeof data.detail==='string'?data.detail:'Login failed');
 if(data.token)setSessionToken(data.token);
 return data;
}
export async function registerApi(data:{name:string;email:string;phone:string;password:string}):Promise<{success:boolean;message:string}>{
 const r=await fetch(base+'/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
 const res=await r.json().catch(()=>({}));
 if(!r.ok)throw Error(typeof res.detail==='string'?res.detail:'Registration failed');
 return res;
}
export async function verifyOtpApi(data:{email:string;otp:string;name?:string;phone?:string;password?:string}):Promise<{success:boolean;user:AuthUser;token:string}>{
 const r=await fetch(base+'/auth/verify-otp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
 const res=await r.json().catch(()=>({}));
 if(!r.ok)throw Error(typeof res.detail==='string'?res.detail:'OTP verification failed');
 if(res.token)setSessionToken(res.token);
 return res;
}
export async function forgotPasswordApi(email:string):Promise<{success:boolean;message:string}>{
 const r=await fetch(base+'/auth/forgot-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email})});
 const res=await r.json().catch(()=>({}));
 if(!r.ok)throw Error(typeof res.detail==='string'?res.detail:'Password reset failed');
 return res;
}
export async function checkBackendStatus():Promise<{connected:boolean;version?:string}>{
 try{
  const r=await fetch(base+'/health',{signal:AbortSignal.timeout(4000)});
  if(r.ok){const d=await r.json();return {connected:true,version:d.version};}
 }catch{}
 return {connected:false};
}
export const caregivers=()=>api<Caregiver[]>('/caregivers');
export const triage=(body:unknown)=>api<{request_id:string;result:Result}>('/ui/triage',body);

export type StructuredFacts={
  patient_target:string;
  age_group:string;
  symptoms:string[];
  duration:string;
  severity:string;
  warning_signs:Record<string,string>;
  existing_conditions:string[];
  allergies_medications:string[];
  family_history?:{relation:string;condition:string;duration?:string}[];
  uploaded_documents?:{doc_type:string;summary:string;date?:string;provider?:string}[];
  care_preference:string;
  uncertainties:string[];
  updated_at?:string;
};

export type AssistantMessage={
  id:string;
  role:'user'|'assistant';
  text:string;
  created:string;
  metadata?:{
    is_emergency?:boolean;
    sources?:{title:string;url:string}[];
    red_flags?:string[];
    follow_up_question?:string|null;
    chips?:string[];
    care_pathway_hint?:string|null;
    has_image?:boolean;
    mime?:string;
    next_action?:{
      type:string;
      label:string;
      request_id?:string;
      route?:string;
    }|null;
  };
};

export type AssistantStatus={
  configured:boolean;
  provider:string;
  memory_provider:string;
  supported_languages:string[];
  message:string;
};

export type AssistantChatResponse={
  message:string;
  sources?:{title:string;url:string}[];
  language?:string;
  follow_up_question:string|null;
  structured_facts:StructuredFacts;
  care_recommendation:(Result&{request_id:string})|null;
  suggested_chips:string[];
  next_action:{
    type:string;
    label:string;
    request_id?:string;
    route?:string;
  }|null;
  is_emergency:boolean;
};

export type AssistantConversation={
  messages:AssistantMessage[];
  structured_facts:StructuredFacts;
  care_recommendation:(Result&{request_id:string})|null;
};

export const assistantStatus=()=>api<AssistantStatus>('/assistant/status');
export const assistantConversation=()=>api<AssistantConversation>('/assistant/conversation');
export const assistantChat=(body:{message:string;language?:string;location?:{lat:number;lng:number}|null;image_base64?:string|null;image_mime_type?:string|null})=>api<AssistantChatResponse>('/assistant/chat',body);
export const assistantCorrectFacts=(facts:StructuredFacts)=>api<{updated:boolean;structured_facts:StructuredFacts}>('/assistant/facts/correct',{facts});
export const assistantClear=()=>api<{cleared:boolean}>('/assistant/conversation',undefined,'DELETE');
