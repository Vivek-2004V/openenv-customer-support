"use client";

import { useState, useEffect } from 'react';

const API_URL = typeof window !== 'undefined' 
  ? (window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1') 
    ? 'http://127.0.0.1:7860' 
    : window.location.origin) 
  : "http://127.0.0.1:7860";

export default function Home() {
  const [state, setState] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [booting, setBooting] = useState(true);
  const [bootAttempt, setBootAttempt] = useState(0);
  const [actionInput, setActionInput] = useState('{\n  "action_type": "classify_ticket",\n  "payload": { "classification": "refund" }\n}');
  const [logs, setLogs] = useState<any[]>([]);
  const [score, setScore] = useState<number | null>(null);
  const [statusMsg, setStatusMsg] = useState<{ text: string, type: 'success' | 'error' } | null>(null);

  const showStatus = (text: string, type: 'success' | 'error') => {
    setStatusMsg({ text, type });
    setTimeout(() => setStatusMsg(null), 5000);
  };

  const addLog = (message: string, role: string, info = '', status = '') => {
    setLogs(prev => [...prev.slice(-19), { role, message, info, status }]);
  };

  const fetchState = async () => {
    try {
      const res = await fetch(`${API_URL}/state`);
      if (res.ok) {
        const data = await res.json();
        const obs = data.observation || data.state || data;
        if (obs && obs.status !== "session_complete") {
          setState(obs);
          setBooting(false);
          return true;
        }
      }
    } catch (e) {
      console.error(e);
    }
    return false;
  };

  const resetEnv = async () => {
    setLoading(true);
    setScore(null);
    try {
      const res = await fetch(`${API_URL}/reset`, { method: 'POST' });
      const data = await res.json();
      const obs = data.observation || data.state || data;
      setState(obs);
      setLogs([{ role: 'system', message: 'Environment Reset Successfully' }]);
      showStatus("Enterprise session initialized.", "success");
      setBooting(false);
    } catch (e) {
      showStatus("Connection failed. Ensure backend is running.", "error");
    }
    setLoading(false);
  };

  const boot = async () => {
    setBootAttempt(prev => prev + 1);
    const success = await fetchState();
    if (success) {
      addLog('Backend connected — session restored', 'system');
    } else {
      try {
        const res = await fetch(`${API_URL}/reset`, { method: 'POST' });
        if (res.ok) {
          const data = await res.json();
          const obs = data.observation || data.state || data;
          setState(obs);
          setBooting(false);
          addLog('Backend connected — session started', 'system');
        } else {
          setTimeout(boot, 2000);
        }
      } catch {
        setTimeout(boot, 2000);
      }
    }
  };

  const sendAction = async () => {
    setLoading(true);
    try {
      let actionObj;
      try {
        actionObj = JSON.parse(actionInput.trim());
      } catch (e) {
        throw new Error("Invalid JSON format.");
      }

      const res = await fetch(`${API_URL}/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(actionObj)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Step failed.");

      const obs = data.observation || data.state || data;
      setState(obs);

      if (obs?.status === "session_complete") {
        addLog('🎉 Session Complete!', 'system');
        showStatus("Session finished!", "success");
      } else {
        const reward = data.reward ?? 0;
        const msg = data.info?.message || "Action processed";
        addLog(`Action: ${actionObj.action_type}`, 'agent', `${msg} | Reward: ${reward.toFixed(3)}`, reward >= 0 ? "success" : "failed");
        showStatus(`Action: ${reward >= 0 ? 'SUCCESS' : 'DEDUCTION'}`, reward >= 0 ? "success" : "error");
      }
    } catch (e: any) {
      showStatus(e.message || "Network Error.", "error");
    }
    setLoading(false);
  };

  const runHardGrader = async () => {
    setLoading(true);
    setScore(null);
    try {
      const res = await fetch(`${API_URL}/grader?task_id=task_hard_1`);
      const data = await res.json();
      setScore(data.score ?? 0);
      addLog(`Evaluation Score: ${(data.score * 100).toFixed(0)}%`, 'system');
      showStatus("Evaluation complete.", "success");
    } catch (e: any) {
      showStatus("Grader unavailable.", "error");
    }
    setLoading(false);
  };

  useEffect(() => {
    boot();
  }, []);

  return (
    <main className="container animate-slide">
      <header style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--card-border)', paddingBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.025em', color: 'var(--foreground)', margin: 0 }}>
            OpenEnv <span style={{ color: 'var(--primary)' }}>Enterprise</span>
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: '1.1rem', margin: '0.25rem 0 0 0' }}>AI Decision Monitoring System</p>
        </div>
        <div style={{ textAlign: 'right' }}>
           <button className="btn btn-outline" onClick={resetEnv} disabled={loading || booting}>
            {loading ? 'Processing...' : 'New Session'}
          </button>
        </div>
      </header>

      {statusMsg && (
        <div style={{ 
          position: 'fixed', top: '20px', right: '20px', zIndex: 1000, 
          padding: '1rem 2rem', borderRadius: '12px', 
          background: statusMsg.type === 'success' ? '#10b981' : '#ef4444', 
          color: 'white', fontWeight: 700, boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
          display: 'flex', alignItems: 'center', gap: '10px'
        }}>
          {statusMsg.type === 'success' ? '✅' : '❌'} {statusMsg.text}
        </div>
      )}

      <div className="layout-grid">
        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div className="glass-card">
            {booting ? (
              <div style={{ textAlign: 'center', padding: '5rem' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1.5rem', animation: 'spin 2s linear infinite', display: 'inline-block' }}>⚙️</div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Starting Engine</h2>
                <p style={{ color: 'var(--muted)' }}>Connecting to backend... Attempt {bootAttempt}</p>
              </div>
            ) : state && state?.status !== "session_complete" ? (
              <div style={{ display: 'grid', gap: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                   <div style={{ flex: 1 }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase' }}>Current Ticket</span>
                    <p style={{ marginTop: '0.5rem', fontSize: '1.4rem', fontWeight: 600 }}>"{state?.ticket_text || 'Loading...'}"</p>
                  </div>
                  <div style={{ textAlign: 'right', minWidth: '100px' }}>
                     <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--muted)' }}>SLA</div>
                     <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{state?.steps_taken || 0} / {state?.sla_limit || 10}</div>
                  </div>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                  {['sentiment', 'priority', 'status'].map(key => (
                    <div key={key} className="glass-card" style={{ padding: '0.75rem', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>{key}</div>
                      <div className={`badge badge-${state?.[key] || 'neutral'}`} style={{ fontSize: '0.7rem', marginTop: '0.25rem' }}>{state?.[key] || 'OPEN'}</div>
                    </div>
                  ))}
                  <div className="glass-card" style={{ padding: '0.75rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>Reward</div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 900, color: 'var(--primary)' }}>+{(state?.total_reward || 0).toFixed(2)}</div>
                  </div>
                </div>
              </div>
            ) : state?.status === "session_complete" ? (
              <div style={{ textAlign: 'center', padding: '4rem' }}>
                <div style={{ fontSize: '4rem' }}>🎉</div>
                <h2 style={{ fontSize: '2rem', fontWeight: 800 }}>Queue Completed</h2>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '3rem', marginTop: '2rem' }}>
                    <div><div style={{ color: 'var(--muted)', fontWeight: 700 }}>RESOLVED</div><div style={{ fontSize: '2rem', fontWeight: 900 }}>{state?.resolved || 0}</div></div>
                    <div><div style={{ color: 'var(--muted)', fontWeight: 700 }}>TOTAL REWARD</div><div style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--primary)' }}>{(state?.total_reward || 0).toFixed(2)}</div></div>
                </div>
                <button className="btn" style={{ marginTop: '2rem' }} onClick={resetEnv}>Start New Session</button>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '5rem', color: 'var(--muted)' }}>Initializing Enterprise Service...</div>
            )}
          </div>

          <div className="glass-card">
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1rem' }}>Control Center</h2>
            <textarea 
              value={actionInput} onChange={(e) => setActionInput(e.target.value)}
              rows={5} style={{ fontSize: '0.9rem', fontFamily: 'monospace', marginBottom: '1.5rem' }}
            />
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button className="btn" onClick={sendAction} disabled={loading || booting || !state} style={{ flex: 2 }}>
                {loading ? 'Executing...' : 'Execute Action'}
              </button>
              <button className="btn btn-outline" onClick={runHardGrader} disabled={loading || booting || !state} style={{ flex: 1 }}>Grade</button>
            </div>
          </div>
        </section>

        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
           <div className="glass-card" style={{ flex: 1, maxHeight: '400px', display: 'flex', flexDirection: 'column' }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Support Queue</h2>
              <div style={{ flex: 1, overflowY: 'auto' }}>
                 {state?.info?.queue?.map((q: string, i: number) => (
                   <div key={i} style={{ padding: '0.75rem', borderBottom: '1px solid var(--card-border)', fontSize: '0.85rem', opacity: i === 0 ? 1 : 0.6 }}>
                      #{i+1}: {q}
                   </div>
                 )) || <div style={{ color: 'var(--muted)' }}>Queue is empty</div>}
              </div>
           </div>

           <div className="glass-card" style={{ height: '350px', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Activity Logs</h2>
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column-reverse', gap: '0.5rem' }}>
              {logs.map((log, i) => (
                <div key={i} className={`log-entry ${log.role === 'agent' ? 'log-agent' : 'log-customer'}`}>
                  <div style={{ fontSize: '0.6rem', fontWeight: 900, opacity: 0.5 }}>{log.role.toUpperCase()}</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{log.message}</div>
                  {log.info && <div style={{ fontSize: '0.7rem', color: 'var(--primary)' }}>{log.info}</div>}
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
