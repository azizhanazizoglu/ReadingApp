import React from 'react';

export interface ChangeDiff {
  key: string;
  before: string | string[] | undefined;
  after: string | string[] | undefined;
}

interface Props {
  snapshotBefore: Record<string, any> | null;
  current: Record<string, any>;
  darkMode?: boolean;
  borderColor: string;
  textSub: string;
}

const shallowNormalize = (v: any) => {
  if (Array.isArray(v)) return v.filter(Boolean).join(', ');
  if (v && typeof v === 'object') return JSON.stringify(v);
  return v ?? '';
};

const ConfigChangeViewer: React.FC<Props> = ({ snapshotBefore, current, darkMode, borderColor, textSub }) => {
  const diffs = React.useMemo<ChangeDiff[]>(() => {
    if (!snapshotBefore) return [];
    const out: ChangeDiff[] = [];
    const keys = new Set([...Object.keys(snapshotBefore.fieldSelectors||{}), ...Object.keys(current.fieldSelectors||{})]);
    for (const k of keys) {
      const before = (snapshotBefore.fieldSelectors||{})[k];
      const after = (current.fieldSelectors||{})[k];
      const normBefore = Array.isArray(before)? before.join('\n'): before;
      const normAfter = Array.isArray(after)? after.join('\n'): after;
      if (normBefore !== normAfter) out.push({ key: k, before, after });
    }
    return out.sort((a,b)=> a.key.localeCompare(b.key));
  }, [snapshotBefore, current]);

  if (!snapshotBefore) return null;
  if (!diffs.length) return <div style={{ fontSize:11, color: textSub, padding:'4px 6px' }}>No changes since last save.</div>;

  return (
    <div style={{ border:`1px solid ${borderColor}`, borderRadius:8, marginTop:8, maxHeight:180, overflow:'auto', fontSize:11 }}>
      <div style={{ position:'sticky', top:0, background: darkMode? '#0f172a':'#f8fafc', padding:'4px 6px', fontWeight:600 }}>Changed Fields ({diffs.length})</div>
      {diffs.map(d => (
        <div key={d.key} style={{ display:'grid', gridTemplateColumns:'120px 1fr 1fr', gap:6, padding:'4px 6px', borderTop:`1px solid ${borderColor}` }}>
          <div style={{ fontWeight:500 }}>{d.key}</div>
          <div style={{ whiteSpace:'pre-line', color:'#dc2626' }}>{shallowNormalize(d.before)}</div>
          <div style={{ whiteSpace:'pre-line', color:'#16a34a' }}>{shallowNormalize(d.after)}</div>
        </div>
      ))}
    </div>
  );
};

export default ConfigChangeViewer;
