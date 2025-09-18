import React from 'react';

interface Props {
  criticalFields: string[];
  setCriticalFields: (v: string[]) => void;
  inputBg: string;
  inputBorder: string;
  textSub: string;
}

const CriticalFieldsEditor: React.FC<Props> = ({ criticalFields, setCriticalFields, inputBg, inputBorder, textSub }) => {
  return (
    <div style={{ marginTop:10 }}>
      <div style={{ fontSize:12, color:textSub, marginBottom:4 }}>Critical fields (comma-separated):</div>
      <input value={criticalFields.join(',')} onChange={e=> setCriticalFields(e.target.value.split(',').map(s=>s.trim()).filter(Boolean))} style={{ width:'100%', fontSize:12, padding:'8px 10px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10 }} />
    </div>
  );
};

export default CriticalFieldsEditor;
