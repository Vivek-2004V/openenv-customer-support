"use client";

import { useState, useEffect } from 'react';

const API_URL = "http://127.0.0.1:7860";

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
        setState(data.state);
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
      const actionObj = JSON.parse(actionInput);
      const res = await fetch(`${API_URL}/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(actionObj)
      });
      const data = await res.json();
      setState(data.observation.state);
      setLogs(prev => [...prev, {
        role: 'agent', 
        message: `Executed: ${actionObj.action_type}`,
        info: `Reward: ${data.reward.value} | Done: ${data.done}`
      }]);
    } catch (e) {
      alert("Invalid JSON action format or Network Error.");
    }
    setLoading(false);
  };

  const runHardGrader = async () => {
    try {
      const res = await fetch(`${API_URL}/grader?task_id=task_hard_1`);
      const data = await res.json();
      setScore(data.score);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchState();
  }, []);

  return (
    <main className="container animate-fade-in">
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ color: 'var(--primary)' }}>OpenEnv Dashboard</h1>
        <p style={{ opacity: 0.7 }}>AI Customer Support Simulation</p>
      </header>

      <div className="layout-grid">
        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2>Active Environment State</h2>
              <button className="btn btn-outline" onClick={resetEnv} disabled={loading}>
                {loading ? 'Processing...' : 'Reset Environment'}
              </button>
            </div>

            {state ? (
              <div style={{ display: 'grid', gap: '1rem' }}>
                <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '8px' }}>
                  <span style={{ fontSize: '0.8rem', opacity: 0.7, textTransform: 'uppercase' }}>Incoming Ticket Log</span>
                  <p style={{ marginTop: '0.5rem', fontSize: '1.1rem', fontWeight: 500 }}>"{state.ticket_text}"</p>
                </div>
                
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                  <div className="glass-card" style={{ flex: 1, padding: '12px' }}>
                    <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>Sentiment</div>
                    <div className={`badge badge-${state.sentiment}`} style={{ display: 'inline-block', marginTop: '4px' }}>
                      {state.sentiment}
                    </div>
                  </div>
                  <div className="glass-card" style={{ flex: 1, padding: '12px' }}>
                    <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>Priority</div>
                    <div style={{ fontWeight: 600, color: 'var(--warning)', marginTop: '4px', textTransform: 'capitalize' }}>
                      {state.priority || 'Unassigned'}
                    </div>
                  </div>
                  <div className="glass-card" style={{ flex: 1, padding: '12px' }}>
                    <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>Status</div>
                    <div className={`badge badge-${state.status}`} style={{ display: 'inline-block', marginTop: '4px' }}>
                      {state.status}
                    </div>
                  </div>
                </div>

                <div className="glass-card">
                  <h3 style={{ fontSize: '1rem' }}>System Variables</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                    <div>
                      <div style={{ opacity: 0.7, fontSize: '0.8rem' }}>Classification</div>
                      <div style={{ fontWeight: 500 }}>{state.classification || 'Unassigned'}</div>
                    </div>
                    <div>
                      <div style={{ opacity: 0.7, fontSize: '0.8rem' }}>Steps Tracked</div>
                      <div style={{ fontWeight: 500 }}>{state.steps_taken} / 10</div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '2rem', opacity: 0.5 }}>
                No active environment. Click Reset.
              </div>
            )}
          </div>

          <div className="glass-card">
            <h2>Send Action (JSON Payload)</h2>
            <textarea 
              value={actionInput}
              onChange={(e) => setActionInput(e.target.value)}
              rows={5}
              style={{ fontFamily: 'monospace', marginBottom: '1rem' }}
            />
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button className="btn" onClick={sendAction} disabled={loading || !state || state.status === 'closed'}>
                Execute Action
              </button>
              <button className="btn btn-success" onClick={runHardGrader} disabled={loading || !state}>
                Grade Execution
              </button>
            </div>

            {score !== null && (
              <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(34, 197, 94, 0.1)', border: '1px solid var(--success)', borderRadius: '8px' }}>
                <strong style={{ color: 'var(--success)' }}>HARD TASK GRADING SCORE: </strong> 
                <span style={{ fontSize: '1.2rem', fontWeight: 800 }}>{(score * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>

        </section>

        <section>
          <div className="glass-card" style={{ height: '100%' }}>
            <h2>Execution Log</h2>
            <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {logs.length === 0 ? (
                <div style={{ opacity: 0.5, textAlign: 'center', padding: '1rem' }}>Awaiting Actions...</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className={`log-entry ${log.role === 'agent' ? 'log-agent' : 'log-customer'}`}>
                    <div style={{ fontWeight: 600 }}>{log.message}</div>
                    {log.info && <div style={{ fontSize: '0.8rem', opacity: 0.7, marginTop: '4px' }}>{log.info}</div>}
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
