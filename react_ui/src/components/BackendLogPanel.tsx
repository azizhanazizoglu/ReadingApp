import React, { useEffect, useState } from "react";

export const BackendLogPanel: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch("http://localhost:5001/api/logs");
        const data = await res.json();
        setLogs(data.logs || []);
      } catch (e) {
        setLogs(["[ERROR] Backend logları alınamadı."]);
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 2000); // 2 sn'de bir güncelle
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{
      position: 'fixed',
      left: 0,
      right: 0,
      bottom: 0,
      margin: '0 auto',
      maxWidth: 800,
      background: 'rgba(0,0,0,0.85)',
      color: '#E6F0FA',
      fontSize: 13,
      borderRadius: 8,
      padding: '8px 16px',
      zIndex: 9999,
      boxShadow: '0 0 12px #223A5E',
      minHeight: 36,
      maxHeight: 120,
      overflowY: 'auto',
      textAlign: 'left',
    }}>
      <b>Backend Logları:</b>
      <ul style={{margin: 0, padding: 0, listStyle: 'none'}}>
        {logs.slice(-6).map((log, i) => (
          <li key={i} style={{whiteSpace: 'pre-wrap'}}>{log}</li>
        ))}
      </ul>
    </div>
  );
};
