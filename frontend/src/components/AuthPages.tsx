import React,{useState,useRef,useEffect} from 'react';
import {Brand} from './Brand';
import {HeartPulse,Eye,EyeOff,ArrowRight,Phone,Mail,User,Lock,ShieldCheck,CheckCircle2,RotateCcw,Loader2,TriangleAlert,Server} from 'lucide-react';
import {loginApi,registerApi,verifyOtpApi,forgotPasswordApi,checkBackendStatus} from '../lib/api';

// ─── Demo Credentials ────────────────────────────────────────────────────────
export const DEMO_USERS:{[email:string]:{password:string;name:string;phone:string}}={
  'demo@triagegrid.in':{password:'TG@demo2024',name:'Aarav Sharma',phone:'+91 98765 43210'},
  'test@carecompass.in':{password:'Care@1234',name:'Priya Nair',phone:'+91 91234 56789'},
};
export const DEMO_OTP='112233';

type AuthPage='login'|'register'|'otp'|'forgot';
type AuthMode={page:AuthPage;email?:string;phone?:string;name?:string;fromRegister?:boolean};

interface AuthScreenProps{onAuth:(name:string,email:string)=>void;}

function OtpInput({value,onChange}:{value:string;onChange:(v:string)=>void}){
  const refs=Array.from({length:6},()=>useRef<HTMLInputElement>(null));
  const digits=value.padEnd(6,' ').split('');
  function handleKey(i:number,e:React.KeyboardEvent<HTMLInputElement>){
    if(e.key==='Backspace'&&!digits[i].trim()&&i>0){refs[i-1].current?.focus();}
  }
  function handleChange(i:number,v:string){
    const d=v.replace(/\D/,'');
    const next=digits.map((c,idx)=>idx===i?d:c).join('').replace(/ /g,'');
    onChange(next.slice(0,6));
    if(d&&i<5)refs[i+1].current?.focus();
  }
  return(
    <div style={{display:'flex',gap:10,justifyContent:'center',margin:'24px 0'}}>
      {digits.map((d,i)=>(
        <input key={i} ref={refs[i]} type="text" inputMode="numeric" maxLength={1}
          value={d.trim()} onChange={e=>handleChange(i,e.target.value)}
          onKeyDown={e=>handleKey(i,e)}
          style={{width:48,height:56,textAlign:'center',fontSize:22,fontWeight:700,
            borderRadius:14,border:`2px solid ${d.trim()?'#2b6be7':'#dce6f5'}`,
            background:d.trim()?'#f0f6ff':'#fafcff',color:'#1a3a6e',outline:'none',
            transition:'border-color .15s,background .15s'}}/>
      ))}
    </div>
  );
}

export default function AuthScreen({onAuth}:AuthScreenProps){
  const [mode,setMode]=useState<AuthMode>({page:'login'});
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [showPass,setShowPass]=useState(false);
  const [name,setName]=useState('');
  const [phone,setPhone]=useState('');
  const [confirmPass,setConfirmPass]=useState('');
  const [otp,setOtp]=useState('');
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [backendOnline,setBackendOnline]=useState<boolean|null>(null);
  const [otpTimer,setOtpTimer]=useState(30);
  const timerRef=useRef<ReturnType<typeof setInterval>|null>(null);

  // Check backend health on mount
  useEffect(()=>{
    checkBackendStatus().then(st=>setBackendOnline(st.connected)).catch(()=>setBackendOnline(false));
  },[]);

  // OTP countdown
  useEffect(()=>{
    if(mode.page==='otp'){
      setOtpTimer(30);
      timerRef.current=setInterval(()=>setOtpTimer(t=>t>0?t-1:0),1000);
    }
    return()=>{if(timerRef.current)clearInterval(timerRef.current);};
  },[mode.page]);

  function startTimer(){
    if(timerRef.current)clearInterval(timerRef.current);
    setOtpTimer(30);
    timerRef.current=setInterval(()=>setOtpTimer(t=>t>0?t-1:0),1000);
  }

  async function handleLogin(e:React.FormEvent){
    e.preventDefault();setError('');setBusy(true);
    try{
      const res=await loginApi(email.trim().toLowerCase(),password);
      setBusy(false);
      onAuth(res.user.name,res.user.email);
    }catch(err){
      setBusy(false);
      // Fallback check against local DEMO_USERS in case server network blip
      const fallback=DEMO_USERS[email.trim().toLowerCase()];
      if(fallback&&fallback.password===password){
        onAuth(fallback.name,email.trim().toLowerCase());
        return;
      }
      setError((err as Error).message||'Galat email ya password hai.');
    }
  }

  async function handleRegister(e:React.FormEvent){
    e.preventDefault();setError('');
    if(!name.trim()){setError('Apna naam daalo.');return;}
    if(!email.trim()||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){setError('Valid email daalo.');return;}
    if(!phone.trim()||phone.replace(/\D/g,'').length<10){setError('Valid 10-digit phone number daalo.');return;}
    if(password.length<8){setError('Password kam se kam 8 characters ka hona chahiye.');return;}
    if(password!==confirmPass){setError('Dono passwords match nahi kar rahe.');return;}
    setBusy(true);
    try{
      await registerApi({name:name.trim(),email:email.trim().toLowerCase(),phone:phone.trim(),password});
      setBusy(false);
      setMode({page:'otp',email:email.trim().toLowerCase(),phone:phone.trim(),name:name.trim(),fromRegister:true});
      setOtp('');
    }catch(err){
      setBusy(false);
      setError((err as Error).message||'Registration failed.');
    }
  }

  async function handleOtp(e:React.FormEvent){
    e.preventDefault();setError('');
    if(otp.length<6){setError('6-digit OTP daalo.');return;}
    setBusy(true);
    try{
      const res=await verifyOtpApi({
        email:(mode.email||email).trim().toLowerCase(),
        otp,
        name:mode.name||name,
        phone:mode.phone||phone,
        password
      });
      setBusy(false);
      onAuth(res.user.name,res.user.email);
    }catch(err){
      setBusy(false);
      if(otp===DEMO_OTP){
        onAuth(mode.name||name||'User',(mode.email||email).trim().toLowerCase());
        return;
      }
      setError((err as Error).message||`Galat OTP. Demo ke liye use karo: ${DEMO_OTP}`);
    }
  }

  async function handleForgot(e:React.FormEvent){
    e.preventDefault();setError('');setBusy(true);
    try{
      await forgotPasswordApi(email.trim().toLowerCase());
      setBusy(false);
      setMode({page:'otp',email:email.trim().toLowerCase(),fromRegister:false});
      setOtp('');
    }catch(err){
      setBusy(false);
      setError((err as Error).message||'Password reset failed.');
    }
  }

  const DemoHint=()=>(
    <div style={{background:'#fffbeb',border:'1px solid #fde68a',borderRadius:14,padding:'12px 16px',margin:'16px 0',fontSize:12,color:'#92400e'}}>
      <b style={{display:'flex',alignItems:'center',gap:6,marginBottom:6,fontSize:13}}>
        <ShieldCheck size={15}/>Demo Credentials
      </b>
      <div style={{display:'grid',gap:4}}>
        <span>📧 <b>demo@triagegrid.in</b> / <b>TG@demo2024</b></span>
        <span>📧 <b>test@carecompass.in</b> / <b>Care@1234</b></span>
        <span style={{marginTop:4,color:'#78350f'}}>OTP (har jagah): <b style={{letterSpacing:3}}>112233</b></span>
      </div>
    </div>
  );

  return(
    <div style={{minHeight:'100dvh',background:'linear-gradient(145deg,#e8f0fe 0%,#f1f5fd 40%,#e5f0ff 100%)',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',padding:'20px 16px'}}>
      {/* Decorative blobs */}
      <div style={{position:'fixed',top:-80,right:-80,width:280,height:280,borderRadius:'50%',background:'radial-gradient(circle,#4a8df830,transparent 70%)',pointerEvents:'none'}}/>
      <div style={{position:'fixed',bottom:-60,left:-60,width:220,height:220,borderRadius:'50%',background:'radial-gradient(circle,#7c5af630,transparent 70%)',pointerEvents:'none'}}/>

      {/* Logo Header */}
      <div style={{marginBottom:28,textAlign:'center'}}>
        <div style={{display:'inline-flex',alignItems:'center',gap:12,background:'linear-gradient(120deg,#4872e1,#5d8bef)',borderRadius:20,padding:'14px 24px',boxShadow:'0 8px 32px #3a72e428',marginBottom:12}}>
          <div style={{display:'grid',placeItems:'center',width:40,height:40,borderRadius:13,background:'#ffffff25',border:'1px solid #ffffff40'}}>
            <HeartPulse size={22} color="white"/>
          </div>
          <div>
            <div style={{fontFamily:"'Plus Jakarta Sans',sans-serif",fontWeight:800,fontSize:20,color:'white',letterSpacing:'-0.5px'}}>
              TriageGrid
            </div>
            <div style={{fontSize:9,color:'#c6fff0',letterSpacing:'0.12em',fontWeight:600,marginTop:1}}>CARE · NAVIGATE · CONNECT</div>
          </div>
        </div>
        <p style={{color:'#5e7aa5',fontSize:13,margin:0}}>AI-powered healthcare navigation</p>
        <div style={{marginTop:10}}>
          <span style={{display:'inline-flex',alignItems:'center',gap:6,background:backendOnline?'#ecfdf5':'#fffbeb',border:`1px solid ${backendOnline?'#a7f3d0':'#fde68a'}`,borderRadius:20,padding:'4px 12px',fontSize:11,fontWeight:600,color:backendOnline?'#065f46':'#92400e'}}>
            <span style={{width:7,height:7,borderRadius:'50%',background:backendOnline?'#10b981':'#f59e0b',boxShadow:backendOnline?'0 0 6px #10b981':'none'}}/>
            {backendOnline===null?'Connecting to backend...':backendOnline?'Backend API Connected (Port 8000)':'Connecting to backend...'}
          </span>
        </div>
      </div>

      {/* Auth Card */}
      <div style={{width:'100%',maxWidth:420,background:'white',borderRadius:28,boxShadow:'0 20px 60px #1d427e14,0 2px 8px #1d427e08',padding:'28px 28px 24px',position:'relative',overflow:'hidden'}}>
        {/* Top gradient accent */}
        <div style={{position:'absolute',top:0,left:0,right:0,height:4,background:'linear-gradient(90deg,#4872e1,#85affb,#4872e1)',borderRadius:'28px 28px 0 0'}}/>

        {/* ── LOGIN ── */}
        {mode.page==='login'&&(
          <form onSubmit={handleLogin}>
            <h2 style={{margin:'0 0 4px',fontSize:'1.35em',letterSpacing:'-0.04em',color:'#1a2e4a'}}>Wapas aaye! 👋</h2>
            <p style={{color:'#7a90ad',fontSize:13,margin:'0 0 20px'}}>Apne account mein sign in karo</p>
            <DemoHint/>
            {error&&<div className="error" role="alert" style={{marginBottom:12}}><TriangleAlert size={17}/><div><p style={{margin:0}}>{error}</p></div></div>}
            <label style={{display:'block',marginBottom:16}}>
              <span style={{fontSize:12,fontWeight:600,color:'#52657f',display:'flex',alignItems:'center',gap:6,marginBottom:7}}>
                <Mail size={14}/>Email address
              </span>
              <div style={{position:'relative'}}>
                <input type="email" value={email} onChange={e=>{setEmail(e.target.value);setError('');}} placeholder="demo@triagegrid.in" required autoComplete="email"
                  style={{paddingLeft:14,marginTop:0}}/>
              </div>
            </label>
            <label style={{display:'block',marginBottom:8}}>
              <span style={{fontSize:12,fontWeight:600,color:'#52657f',display:'flex',alignItems:'center',gap:6,marginBottom:7}}>
                <Lock size={14}/>Password
              </span>
              <div style={{position:'relative'}}>
                <input type={showPass?'text':'password'} value={password} onChange={e=>{setPassword(e.target.value);setError('');}} placeholder="••••••••" required autoComplete="current-password"
                  style={{paddingRight:48,marginTop:0}}/>
                <button type="button" onClick={()=>setShowPass(s=>!s)}
                  style={{position:'absolute',right:12,top:'50%',transform:'translateY(-50%)',background:'none',border:'none',padding:4,color:'#8a9ec4',minHeight:'auto',cursor:'pointer'}}>
                  {showPass?<EyeOff size={18}/>:<Eye size={18}/>}
                </button>
              </div>
            </label>
            <div style={{textAlign:'right',marginBottom:20}}>
              <button type="button" className="textButton" style={{padding:'4px 0',fontSize:12}} onClick={()=>{setMode({page:'forgot'});setError('');}}>
                Password bhool gaye?
              </button>
            </div>
            <button type="submit" className="primary" disabled={busy} style={{margin:0,width:'100%'}}>
              {busy?<Loader2 className="spin" size={18}/>:<ArrowRight size={18}/>}
              {busy?'Signing in…':'Sign In'}
            </button>
            <p style={{textAlign:'center',marginTop:20,fontSize:13,color:'#8a9ec4'}}>
              Naya account?{' '}
              <button type="button" className="textButton" style={{padding:'0 4px',fontSize:13}} onClick={()=>{setMode({page:'register'});setError('');}}>
                Register karo
              </button>
            </p>
          </form>
        )}

        {/* ── REGISTER ── */}
        {mode.page==='register'&&(
          <form onSubmit={handleRegister}>
            <h2 style={{margin:'0 0 4px',fontSize:'1.35em',letterSpacing:'-0.04em',color:'#1a2e4a'}}>Account banao 🏥</h2>
            <p style={{color:'#7a90ad',fontSize:13,margin:'0 0 20px'}}>TriageGrid ke saath apna care journey start karo</p>
            {error&&<div className="error" role="alert" style={{marginBottom:12}}><TriangleAlert size={17}/><div><p style={{margin:0}}>{error}</p></div></div>}
            <label style={{display:'block',marginBottom:14}}>
              <span style={{fontSize:12,fontWeight:600,color:'#52657f',display:'flex',alignItems:'center',gap:6,marginBottom:7}}><User size={14}/>Full Name</span>
              <input type="text" value={name} onChange={e=>{setName(e.target.value);setError('');}} placeholder="Aarav Sharma" required autoComplete="name" style={{marginTop:0}}/>
            </label>
            <label style={{display:'block',marginBottom:14}}>
              <span style={{fontSize:12,fontWeight:600,color:'#52657f',display:'flex',alignItems:'center',gap:6,marginBottom:7}}><Mail size={14}/>Email Address</span>
              <input type="email" value={email} onChange={e=>{setEmail(e.target.value);setError('');}} placeholder="aap@example.com" required autoComplete="email" style={{marginTop:0}}/>
            </label>
            <label style={{display:'block',marginBottom:14}}>
              <span style={{fontSize:12,fontWeight:600,color:'#52657f',display:'flex',alignItems:'center',gap:6,marginBottom:7}}><Phone size={14}/>Mobile Number</span>
              <input type="tel" value={phone} onChange={e=>{setPhone(e.target.value);setError('');}} placeholder="+91 98765 43210" required autoComplete="tel" style={{marginTop:0}}/>
            </label>
            <label style={{display:'block',marginBottom:14}}>
              <span style={{fontSize:12,fontWeight:600,color:'#52657f',display:'flex',alignItems:'center',gap:6,marginBottom:7}}><Lock size={14}/>Password</span>
              <div style={{position:'relative'}}>
                <input type={showPass?'text':'password'} value={password} onChange={e=>{setPassword(e.target.value);setError('');}} placeholder="Min. 8 characters" required autoComplete="new-password"
                  style={{paddingRight:48,marginTop:0}}/>
                <button type="button" onClick={()=>setShowPass(s=>!s)}
                  style={{position:'absolute',right:12,top:'50%',transform:'translateY(-50%)',background:'none',border:'none',padding:4,color:'#8a9ec4',minHeight:'auto',cursor:'pointer'}}>
                  {showPass?<EyeOff size={18}/>:<Eye size={18}/>}
                </button>
              </div>
            </label>
            <label style={{display:'block',marginBottom:20}}>
              <span style={{fontSize:12,fontWeight:600,color:'#52657f',display:'flex',alignItems:'center',gap:6,marginBottom:7}}><Lock size={14}/>Confirm Password</span>
              <input type="password" value={confirmPass} onChange={e=>{setConfirmPass(e.target.value);setError('');}} placeholder="Password dobara daalo" required autoComplete="new-password" style={{marginTop:0}}/>
            </label>
            <div className="infoNote" style={{margin:'0 0 16px',fontSize:11}}>
              <ShieldCheck size={15}/>
              <span>OTP aapke phone/email par bheja jayega (Demo: <b style={{letterSpacing:2}}>112233</b>)</span>
            </div>
            <button type="submit" className="primary" disabled={busy} style={{margin:0,width:'100%'}}>
              {busy?<Loader2 className="spin" size={18}/>:<ArrowRight size={18}/>}
              {busy?'Registering…':'Send OTP & Register'}
            </button>
            <p style={{textAlign:'center',marginTop:16,fontSize:13,color:'#8a9ec4'}}>
              Pehle se account hai?{' '}
              <button type="button" className="textButton" style={{padding:'0 4px',fontSize:13}} onClick={()=>{setMode({page:'login'});setError('');}}>
                Sign in karo
              </button>
            </p>
          </form>
        )}

        {/* ── OTP VERIFICATION ── */}
        {mode.page==='otp'&&(
          <form onSubmit={handleOtp}>
            <div style={{textAlign:'center',marginBottom:20}}>
              <div style={{display:'inline-grid',placeItems:'center',width:64,height:64,borderRadius:20,background:'linear-gradient(135deg,#eef5ff,#d6e8ff)',color:'#2b6be7',marginBottom:14,border:'3px solid white',boxShadow:'0 6px 20px #3a72e420'}}>
                <Phone size={28}/>
              </div>
              <h2 style={{margin:'0 0 6px',fontSize:'1.3em',letterSpacing:'-0.04em',color:'#1a2e4a'}}>OTP Verify karo</h2>
              <p style={{color:'#7a90ad',fontSize:13,margin:0}}>
                6-digit OTP bheja gaya<br/>
                <b style={{color:'#2b6be7'}}>{mode.email||email}</b> par
              </p>
            </div>
            {error&&<div className="error" role="alert" style={{marginBottom:8}}><TriangleAlert size={17}/><div><p style={{margin:0}}>{error}</p></div></div>}
            <div className="infoNote" style={{margin:'0 0 4px',fontSize:11,justifyContent:'center'}}>
              <ShieldCheck size={14}/>Demo OTP: <b style={{letterSpacing:4,fontSize:14}}>112233</b>
            </div>
            <OtpInput value={otp} onChange={v=>{setOtp(v);setError('');}}/>
            <button type="submit" className="primary" disabled={busy||otp.length<6} style={{margin:0,width:'100%'}}>
              {busy?<Loader2 className="spin" size={18}/>:<CheckCircle2 size={18}/>}
              {busy?'Verifying…':'Verify OTP'}
            </button>
            <div style={{textAlign:'center',marginTop:16}}>
              {otpTimer>0?(
                <p style={{fontSize:12,color:'#96a8be',margin:0}}>
                  OTP resend karo <b style={{color:'#2b6be7'}}>{otpTimer}s</b> mein
                </p>
              ):(
                <button type="button" className="textButton" style={{fontSize:12,gap:6}} onClick={()=>{setOtp('');setError('');startTimer();}}>
                  <RotateCcw size={14}/>OTP Resend karo
                </button>
              )}
            </div>
            <button type="button" className="textButton" style={{width:'100%',marginTop:8,fontSize:12}} onClick={()=>{setMode({page:mode.fromRegister?'register':'login'});setError('');}}>
              ← Wapas jao
            </button>
          </form>
        )}

        {/* ── FORGOT PASSWORD ── */}
        {mode.page==='forgot'&&(
          <form onSubmit={handleForgot}>
            <div style={{textAlign:'center',marginBottom:20}}>
              <div style={{display:'inline-grid',placeItems:'center',width:64,height:64,borderRadius:20,background:'linear-gradient(135deg,#fff5f7,#ffd9e4)',color:'#e44372',marginBottom:14,border:'3px solid white',boxShadow:'0 6px 20px #e4437220'}}>
                <Lock size={28}/>
              </div>
              <h2 style={{margin:'0 0 6px',fontSize:'1.3em',letterSpacing:'-0.04em',color:'#1a2e4a'}}>Password Reset</h2>
              <p style={{color:'#7a90ad',fontSize:13,margin:0}}>Apna registered email daalo, hum OTP bhejenge</p>
            </div>
            {error&&<div className="error" role="alert" style={{marginBottom:12}}><TriangleAlert size={17}/><div><p style={{margin:0}}>{error}</p></div></div>}
            <label style={{display:'block',marginBottom:20}}>
              <span style={{fontSize:12,fontWeight:600,color:'#52657f',display:'flex',alignItems:'center',gap:6,marginBottom:7}}><Mail size={14}/>Email Address</span>
              <input type="email" value={email} onChange={e=>{setEmail(e.target.value);setError('');}} placeholder="aap@example.com" required autoComplete="email" style={{marginTop:0}}/>
            </label>
            <button type="submit" className="primary" disabled={busy} style={{margin:0,width:'100%'}}>
              {busy?<Loader2 className="spin" size={18}/>:<ArrowRight size={18}/>}
              {busy?'Sending…':'OTP Bhejo'}
            </button>
            <button type="button" className="textButton" style={{width:'100%',marginTop:12,fontSize:13}} onClick={()=>{setMode({page:'login'});setError('');}}>
              ← Login par wapas jao
            </button>
          </form>
        )}
      </div>

      {/* Footer */}
      <p style={{marginTop:24,fontSize:11,color:'#9aaccb',textAlign:'center',lineHeight:1.6}}>
        <ShieldCheck size={12} style={{verticalAlign:'middle',marginRight:4}}/>
        Synthetic demo only · No real patient data · CAI Dataset
      </p>
    </div>
  );
}
