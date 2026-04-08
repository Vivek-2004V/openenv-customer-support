"use client";

import { useState, useEffect } from 'react';

const API_URL = typeof window !== 'undefined' ? (window.location.origin.includes('localhost') ? 'http://127.0.0.1:7860' : window.location.origin) : "http://127.0.0.1:7860";

export default function Home() {
  const [state, setState] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [actionInput, setActionInput] = useState('{\n  "action_type": "classify_ticket",\n  "payload": { "classification": "refund" }\n}');
  const [logs, setLogs] = useState<any[]>([]);
  const [score, setScore] = useState<number | null>(null);
  const [statusMsg, setStatusMsg] = useState<{ text: string, type: 'success' | 'error' } | null>(null);

  const showStatus = (text: string, type: 'success' | 'error') => {
    setStatusMsg({ text, type });
    setTimeout(() => setStatusMsg(null), 5000);
  };

  const fetchState = async () => {
    try {
      const res = await fetch(`${API_URL}/state`);
      if (res.ok) {
        const data = await res.json();
        if (data.state && data.state.status !== "session_complete") {
          setState(data.state);
        } else {
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
    setStatusMsg(null);
    try {
      const res = await fetch(`${API_URL}/reset`);
      const data = await res.json();
      setState(data.state);
      setLogs([{ role: 'system', message: 'Environment Reset Successfully' }]);
      showStatus("Enterprise session initialized.", "success");
    } catch (e) {
      showStatus("Connection failed. Ensure backend is running.", "error");
    }
    setLoading(false);
  };

  const sendAction = async () => {
    setLoading(true);
    try {
      let actionObj;
      try {
        actionObj = JSON.parse(actionInput.trim());
      } catch (e) {
        throw new Error("Invalid JSON: Fix brackets or commas.");
      }

      const res = await fetch(`${API_URL}/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(actionObj)
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: "Server error" }));
        throw new Error(errorData.detail || "Step failed.");
      }

      const data = await res.json();
      
      if (data.observation.state.status === "session_complete") {
        setLogs(prev => [...prev, { role: 'system', message: '🎉 Session Complete!' }]);
        setState(data.observation.state);
        showStatus("Session finished successfully!", "success");
      } else {
        setState(data.observation.state);
        const stepStatus = data.info.status;
        setLogs(prev => [...prev, {
          role: 'agent', 
          message: `Action: ${actionObj.action_type}`,
          info: `${data.info.message} | Reward: ${data.reward.value.toFixed(2)}`,
          status: stepStatus
        }]);
        showStatus(`Action executed: ${stepStatus.toUpperCase()}`, stepStatus === "failed" ? "error" : "success");
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
      if (!res.ok) throw new Error("Evaluation engine unreachable.");
      const data = await res.json();
      setScore(data.score ?? 0);
      setLogs(prev => [...prev, { role: 'system', message: `📈 Evaluation: ${(data.score * 100).toFixed(0)}%` }]);
      showStatus("Model evaluation complete.", "success");
    } catch (e: any) {
      showStatus(e.message || "Grader connection failed.", "error");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchState();
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
           <button className="btn btn-outline" onClick={resetEnv} disabled={loading}>
            {loading ? 'Processing...' : 'New Session'}
          </button>
        </div>
      </header>

      {statusMsg && (
        <div className={`animate-slide`} style={{ 
          position: 'fixed', 
          top: '20px', 
          right: '20px', 
          zIndex: 1000, 
          padding: '1rem 2rem', 
          borderRadius: '12px', 
          background: statusMsg.type === 'success' ? '#10b981' : '#ef4444', 
          color: 'white', 
          fontWeight: 700, 
          boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          {statusMsg.type === 'success' ? '✅' : '❌'} {statusMsg.text}
        </div>
      )}

      <div className="layout-grid" style={{ gridTemplateColumns: 'minmax(0, 1fr) 350px', gap: '2rem' }}>
        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          <div className="glass-card">
            {state && state.status !== "session_complete" ? (
              <div style={{ display: 'grid', gap: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                   <div style={{ flex: 1 }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Current Instruction</span>
                    <p style={{ marginTop: '0.5rem', fontSize: '1.5rem', fontWeight: 600, lineHeight: 1.4 }}>"{state.ticket_text}"</p>
                  </div>
                  <div style={{ marginLeft: '2rem', textAlign: 'right' }}>
                     <div style={{ fontSize: '0.7rem', fontWeight: 800, color: state.sla_warning ? 'var(--error)' : 'var(--muted)', textTransform: 'uppercase' }}>SLA Health</div>
                     <div style={{ fontSize: '1.5rem', fontWeight: 800, color: state.sla_warning ? 'var(--error)' : 'var(--foreground)' }}>
                       {state.steps_taken} / {state.sla_limit}
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
                    <div className={`badge ${state.priority ? `badge-${state.priority}` : 'badge-unassigned'}`} style={{ fontSize: '0.75rem', width: '100%', textAlign: 'center' }}>{state.priority || 'PENDING'}</div>
                  </div>
                  <div className="glass-card" style={{ padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Status</div>
                    <div className={`badge badge-${state.status}`} style={{ fontSize: '0.75rem', width: '100%', textAlign: 'center' }}>{state.status}</div>
                  </div>
                   <div className="glass-card" style={{ padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Reward</div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 900, textAlign: 'center', color: 'var(--primary)' }}>+{(state.total_reward || 0).toFixed(2)}</div>
                  </div>
                </div>
              </div>
            ) : state?.status === "session_complete" ? (
              <div style={{ textAlign: 'center', padding: '4rem' }}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎉</div>
                <h2 style={{ fontSize: '2rem', fontWeight: 800 }}>Evaluation Finished</h2>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '3rem', marginTop: '2rem' }}>
                   <div>
                     <div style={{ color: 'var(--muted)', fontSize: '0.8rem', fontWeight: 700 }}>RESOLVED</div>
                     <div style={{ fontSize: '2rem', fontWeight: 900 }}>{state.info.resolved}</div>
                   </div>
                   <div>
                     <div style={{ color: 'var(--muted)', fontSize: '0.8rem', fontWeight: 700 }}>TOTAL SCORE</div>
                     <div style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--primary)' }}>{state.info.total_reward.toFixed(2)}</div>
                   </div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '5rem', color: 'var(--muted)' }}>
                Waiting for backend synchronization...
              </div>
            )}
          </div>

          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--foreground)' }}>Control Center</h2>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-outline" style={{ fontSize: '0.7rem', padding: '0.25rem 0.5rem' }} onClick={() => setActionInput('{\n  "action_type": "classify_ticket",\n  "payload": { "classification": "refund" }\n}')}>🏷️ Classify</button>
                <button className="btn btn-outline" style={{ fontSize: '0.7rem', padding: '0.25rem 0.5rem' }} onClick={() => setActionInput('{\n  "action_type": "assign_priority",\n  "payload": { "priority": "high" }\n}')}>⚡ Priority</button>
                <button className="btn btn-outline" style={{ fontSize: '0.7rem', padding: '0.25rem 0.5rem' }} onClick={() => setActionInput('{\n  "action_type": "generate_response",\n  "payload": { "response": "I apologize for the delay, we are fixing this now." }\n}')}>✍️ Reply</button>
                <button className="btn btn-outline" style={{ fontSize: '0.7rem', padding: '0.25rem 0.5rem' }} onClick={() => setActionInput('{\n  "action_type": "resolve",\n  "payload": {}\n}')}>✅ Resolve</button>
              </div>
            </div>
            
            <div style={{ marginBottom: '1.5rem' }}>
               <textarea 
                value={actionInput}
                onChange={(e) => setActionInput(e.target.value)}
                rows={5}
                style={{ fontSize: '0.9rem', fontFamily: 'monospace', padding: '1rem', background: '#f8fafc', borderRadius: '12px' }}
                placeholder="Enter AI Action JSON..."
              />
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button className="btn" onClick={sendAction} disabled={loading || !state || state.status === 'session_complete'} style={{ flex: 2 }}>
                {loading ? 'Executing...' : 'Execute Action'}
              </button>
              <button className="btn btn-outline" onClick={runHardGrader} disabled={loading || !state} style={{ flex: 1 }}>
                Grade Model
              </button>
            </div>
          </div>

          {score !== null && (
            <div className="glass-card animate-slide" style={{ border: '2px solid #10b981', background: '#ecfdf5' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '0.9rem', color: '#065f46', fontWeight: 800, textTransform: 'uppercase' }}>Benchmark Result</h3>
                  <p style={{ margin: '0.25rem 0 0 0', color: '#047857', fontSize: '0.8rem' }}>Hard Task Evaluation Suite</p>
                </div>
                <div style={{ fontSize: '3rem', fontWeight: 950, color: '#059669', letterSpacing: '-0.05em' }}>
                  {(score * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          )}

        </section>

        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
           <div className="glass-card" style={{ flex: 1, maxHeight: '450px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Queue Management</h2>
                <span className="badge" style={{ background: 'var(--primary)', color: 'white', padding: '2px 10px' }}>{state?.info?.queue?.length || 0} Pending</span>
              </div>

              {/* Progress Tracker */}
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', fontWeight: 700, marginBottom: '0.4rem', color: 'var(--muted)' }}>
                  <span>SESSION PROGRESS</span>
                  <span>{((state?.info?.resolved || 0) / 3 * 100).toFixed(0)}%</span>
                </div>
                <div style={{ width: '100%', height: '6px', background: '#f1f5f9', borderRadius: '10px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${((state?.info?.resolved || 0) / 3 * 100)}%`, 
                    height: '100%', 
                    background: 'var(--primary)', 
                    transition: 'width 0.5s ease-out' 
                  }}></div>
                </div>
              </div>

              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                 {state?.info?.queue && state.info.queue.length > 0 ? state.info.queue.map((q: string, i: number) => {
                   const isFirst = i === 0;
                   const difficulty = q.length > 25 ? "HARD" : q.length > 20 ? "MEDIUM" : "EASY";
                   return (
                     <div key={i} className="glass-card" style={{ 
                       padding: '0.75rem', 
                       fontSize: '0.85rem', 
                       background: isFirst ? '#f0f9ff' : 'white', 
                       borderLeft: isFirst ? '4px solid var(--primary)' : '1px solid var(--card-border)',
                       position: 'relative',
                       opacity: isFirst ? 1 : 0.8,
                       animation: isFirst ? 'pulse 2s infinite' : 'none'
                     }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                          <span style={{ fontSize: '0.6rem', fontWeight: 800, color: isFirst ? 'var(--primary)' : 'var(--muted)' }}>
                            {isFirst ? '● ACTIVE NOW' : `UPCOMING #${i + 1}`}
                          </span>
                          <span style={{ fontSize: '0.55rem', fontWeight: 900, color: difficulty === 'HARD' ? 'var(--error)' : 'var(--muted)' }}>
                            {difficulty}
                          </span>
                        </div>
                        <div style={{ fontWeight: 600, color: 'var(--foreground)' }}>{q}</div>
                        <div style={{ marginTop: '0.5rem', fontSize: '0.65rem', color: 'var(--muted)', display: 'flex', gap: '10px' }}>
                          <span>⏱️ {isFirst ? 'Est. 2m' : `${(i+1)*3}m wait`}</span>
                          <span>🏢 Tier 1</span>
                        </div>
                     </div>
                   );
                 }) : (
                   <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>
                      <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🎯</div>
                      <p style={{ fontSize: '0.8rem' }}>Queue Cleared</p>
                   </div>
                 )}
              </div>
           </div>

           <div className="glass-card" style={{ height: '350px', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Activity Logs</h2>
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column-reverse', gap: '0.75rem' }}>
              {logs.map((log, i) => (
                <div key={i} className={`log-entry ${log.role === 'agent' ? 'log-agent' : 'log-customer'}`} style={{ 
                  padding: '0.75rem',
                  borderLeft: log.status === 'success' ? '4px solid #10b981' : log.status === 'failed' ? '4px solid #ef4444' : 'none'
                }}>
                  <div style={{ fontSize: '0.65rem', fontWeight: 900, textTransform: 'uppercase', marginBottom: '0.25rem', opacity: 0.6, display: 'flex', justifyContent: 'space-between' }}>
                    <span>{log.role}</span>
                    {log.status && <span style={{ color: log.status === 'success' ? '#10b981' : '#ef4444' }}>{log.status.toUpperCase()}</span>}
                  </div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>{log.message}</div>
                  {log.info && <div style={{ fontSize: '0.7rem', color: 'var(--primary)', marginTop: '0.25rem', fontWeight: 700 }}>{log.info}</div>}
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
