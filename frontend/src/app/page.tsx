"use client";

import { useState, useEffect } from 'react';

const API_URL = typeof window !== 'undefined' ? (window.location.origin.includes('localhost') ? 'http://127.0.0.1:7860' : window.location.origin) : "http://127.0.0.1:7860";

export default function Home() {
  const [state, setState] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [actionInput, setActionInput] = useState('{\n  "action_type": "classify_ticket",\n  "payload": { "classification": "refund" }\n}');
  const [logs, setLogs] = useState<any[]>([]);
  const [score, setScore] = useState<number | null>(null);

  const fetchState = async () => {
    try {
      const res = await fetch(`${API_URL}/state`);
      if (res.ok) {
        const data = await res.json();
        if (data.state && data.state.status !== "session_complete") {
          setState(data.state);
        } else {
          // No active session or session finished, start new one
          resetEnv();
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const resetEnv = async () => {
    setLoading(true);
    setLogs([]);
    setScore(null);
    try {
      const res = await fetch(`${API_URL}/reset`);
      const data = await res.json();
      setState(data.state);
      setLogs([{ role: 'system', message: 'Environment Reset Successfully' }]);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const sendAction = async () => {
    setLoading(true);
    try {
      // 1. Clean and Parse JSON
      let actionObj;
      try {
        actionObj = JSON.parse(actionInput.trim());
      } catch (e) {
        throw new Error("JSON Parse Error: Please check your brackets and commas.");
      }

      // 2. Execute Fetch
      const res = await fetch(`${API_URL}/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(actionObj)
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: "Unknown server error" }));
        throw new Error(`Server Error: ${errorData.detail || res.statusText}`);
      }

      const data = await res.json();
      
      if (data.observation.state.status === "session_complete") {
        setLogs(prev => [...prev, { role: 'system', message: '🎉 Session Complete! All tickets processed.' }]);
        setState(data.observation.state);
      } else {
        setState(data.observation.state);
        setLogs(prev => [...prev, {
          role: 'agent', 
          message: `Executed: ${actionObj.action_type}`,
          info: `${data.info.message} | Reward: ${data.reward.value.toFixed(2)}`
        }]);
      }
    } catch (e: any) {
      alert(e.message || "Network Error: Could not reach the backend.");
    }
    setLoading(false);
  };

  const runHardGrader = async () => {
    setLoading(true);
    setScore(null);
    try {
      const res = await fetch(`${API_URL}/grader?task_id=task_hard_1`);
      
      if (!res.ok) {
        throw new Error("Grader Error: Could not reach the evaluation engine.");
      }

      const data = await res.json();
      setScore(data.score ?? 0);
      setLogs(prev => [...prev, { role: 'system', message: `📈 Model Evaluation Complete! Score: ${(data.score * 100).toFixed(0)}%` }]);
    } catch (e: any) {
      alert(e.message || "Network Error: Grader failed.");
    }
    setLoading(false);
  };

  useEffect(() => {
    const init = async () => {
      await fetchState();
      // If no active session, auto-initialize
      if (!state) {
        resetEnv();
      }
    };
    init();
  }, []);

  return (
    <main className="container animate-slide">
      <header style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--card-border)', paddingBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.025em', color: 'var(--foreground)', margin: 0 }}>
            OpenEnv <span style={{ color: 'var(--primary)' }}>Enterprise</span>
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: '1.1rem', margin: '0.25rem 0 0 0' }}>AI Customer Support Monitoring & Queue Management</p>
        </div>
        <div style={{ textAlign: 'right' }}>
           <button className="btn btn-outline" onClick={resetEnv} disabled={loading}>
            {loading ? 'Initializing...' : 'New Session'}
          </button>
        </div>
      </header>

      <div className="layout-grid" style={{ gridTemplateColumns: 'minmax(0, 1fr) 350px', gap: '2rem' }}>
        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          <div className="glass-card">
            {state && state.status !== "session_complete" ? (
              <div style={{ display: 'grid', gap: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                   <div style={{ flex: 1 }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Active Ticket</span>
                    <p style={{ marginTop: '0.5rem', fontSize: '1.5rem', fontWeight: 600, lineHeight: 1.4 }}>"{state.ticket_text}"</p>
                  </div>
                  <div style={{ marginLeft: '2rem', textAlign: 'right' }}>
                     <div style={{ fontSize: '0.7rem', fontWeight: 800, color: state.sla_warning ? 'var(--error)' : 'var(--muted)', textTransform: 'uppercase' }}>SLA Deadline</div>
                     <div style={{ fontSize: '1.5rem', fontWeight: 800, color: state.sla_warning ? 'var(--error)' : 'var(--foreground)' }}>
                       {state.steps_taken} / {state.sla_limit} <small style={{ fontSize: '0.8rem', fontWeight: 400 }}>steps</small>
                     </div>
                  </div>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                  <div className="glass-card" style={{ padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Sentiment</div>
                    <div className={`badge badge-${state.sentiment}`} style={{ fontSize: '0.75rem', width: '100%', textAlign: 'center' }}>{state.sentiment}</div>
                  </div>
                  <div className="glass-card" style={{ padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Priority</div>
                    <div className={`badge ${state.priority ? `badge-${state.priority}` : 'badge-unassigned'}`} style={{ fontSize: '0.75rem', width: '100%', textAlign: 'center' }}>{state.priority || 'Wait'}</div>
                  </div>
                  <div className="glass-card" style={{ padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Status</div>
                    <div className={`badge badge-${state.status}`} style={{ fontSize: '0.75rem', width: '100%', textAlign: 'center' }}>{state.status}</div>
                  </div>
                   <div className="glass-card" style={{ padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Ticket ID</div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, textAlign: 'center' }}>#{Math.floor(Math.random() * 9000) + 1000}</div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="glass-card" style={{ background: '#f8fafc', padding: '1rem' }}>
                    <div style={{ color: 'var(--muted)', fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase' }}>Classification</div>
                    <div style={{ fontWeight: 700, marginTop: '0.25rem', color: state.classification ? 'var(--foreground)' : 'var(--muted)' }}>
                      {state.classification || 'Pending Analysis...'}
                    </div>
                  </div>
                  <div className="glass-card" style={{ background: '#f8fafc', padding: '1rem' }}>
                    <div style={{ color: 'var(--muted)', fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase' }}>Session Reward</div>
                    <div style={{ fontWeight: 800, fontSize: '1.2rem', color: 'var(--primary)', marginTop: '0.1rem' }}>
                      {(state.total_reward || 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            ) : state?.status === "session_complete" ? (
              <div style={{ textAlign: 'center', padding: '4rem' }}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🏆</div>
                <h2 style={{ fontSize: '2rem', fontWeight: 800 }}>Session Complete</h2>
                <p style={{ color: 'var(--muted)', marginBottom: '2rem' }}>All tickets have been successfully processed through the pipeline.</p>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '3rem' }}>
                   <div>
                     <div style={{ color: 'var(--muted)', fontSize: '0.8rem', fontWeight: 700 }}>RESOLVED</div>
                     <div style={{ fontSize: '2rem', fontWeight: 900 }}>{state.info.resolved}</div>
                   </div>
                   <div>
                     <div style={{ color: 'var(--muted)', fontSize: '0.8rem', fontWeight: 700 }}>TOTAL REWARD</div>
                     <div style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--primary)' }}>{state.info.total_reward.toFixed(2)}</div>
                   </div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '5rem', color: 'var(--muted)' }}>
                Waiting for enterprise session initialization...
              </div>
            )}
          </div>

          <div className="glass-card">
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
               <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--primary)' }}></span>
               Control Input
            </h2>
            <div style={{ position: 'relative', marginBottom: '1rem' }}>
               <textarea 
                value={actionInput}
                onChange={(e) => setActionInput(e.target.value)}
                rows={4}
                style={{ fontSize: '0.9rem', fontFamily: 'monospace', background: '#f8fafc', border: '1px solid var(--card-border)' }}
              />
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button className="btn" onClick={sendAction} disabled={loading || !state || state.status === 'session_complete'} style={{ flex: 2 }}>
                Execute Action
              </button>
              <button className="btn btn-outline" onClick={runHardGrader} disabled={loading || !state} style={{ flex: 1 }}>
                Grade Model
              </button>
            </div>
            {score !== null && (
              <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#ecfdf5', border: '1px solid #10b981', borderRadius: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, color: '#065f46', fontSize: '0.8rem' }}>Evaluation Score</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 900, color: '#059669' }}>{(score * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>

        </section>

        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
           <div className="glass-card" style={{ flex: 1, minHeight: '350px' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
                Queue <span className="badge" style={{ background: 'var(--primary)', color: 'white' }}>{state?.queue_size || 0}</span>
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                 {state?.info?.queue ? state.info.queue.map((q: string, i: number) => (
                   <div key={i} className="glass-card" style={{ padding: '0.75rem', fontSize: '0.8rem', borderLeft: i === 0 ? '4px solid var(--primary)' : '1px solid var(--card-border)', opacity: i === 0 ? 1 : 0.6 }}>
                      {q}
                   </div>
                 )) : <p style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>Waiting for queue initialization...</p>}
              </div>
           </div>

           <div className="glass-card" style={{ height: '350px', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Activity Logs</h2>
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column-reverse', gap: '0.5rem' }}>
              {logs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)', fontSize: '0.8rem' }}>No activity logged.</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className={`log-entry ${log.role === 'agent' ? 'log-agent' : 'log-customer'}`} style={{ padding: '0.75rem', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '0.6rem', fontWeight: 800, textTransform: 'uppercase' }}>{log.role}</span>
                    </div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{log.message}</div>
                    {log.info && <div style={{ fontSize: '0.7rem', color: 'var(--primary)', marginTop: '0.25rem' }}>{log.info}</div>}
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
