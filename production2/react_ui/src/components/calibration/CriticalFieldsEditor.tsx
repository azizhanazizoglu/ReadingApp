import React from 'react';

interface Props {
  criticalFields: string[];
  setCriticalFields: (v: string[]) => void;
  availableFields?: string[]; // Available fields to show as suggestions
  inputBg: string;
  inputBorder: string;
  chipBorder: string;
  textSub: string;
  darkMode: boolean;
}

const CriticalFieldsEditor: React.FC<Props> = ({ criticalFields, setCriticalFields, availableFields = [], inputBg, inputBorder, chipBorder, textSub, darkMode }) => {
  
  const removeCriticalField = (fieldToRemove: string) => {
    setCriticalFields(criticalFields.filter(f => f !== fieldToRemove));
  };

  return (
    <div style={{ marginTop:10 }}>
      <div style={{ fontSize:12, color:textSub, marginBottom:4 }}>Critical fields (comma-separated):</div>
      
      {/* Show current critical fields as draggable chips with delete buttons */}
      {criticalFields.length > 0 && (
        <div style={{ display:'flex', gap:6, flexWrap:'wrap', marginBottom:8, padding:8, border:`1px solid ${inputBorder}`, borderRadius:10, background: darkMode?'rgba(2,6,23,0.35)':'#ffffff' }}>
          {criticalFields.map((field, idx) => (
            <div key={`critical-${field}-${idx}`} style={{ display:'flex', alignItems:'center', gap:4 }}>
              <div draggable style={{ cursor:'grab', fontSize:11, padding:'6px 10px', border:`1px solid ${chipBorder}`, borderRadius:16, background: darkMode?'#0b1220':'#eef2ff' }}>
                ☰ {field}
              </div>
              <button 
                title={`Remove ${field} from critical fields`}
                onClick={() => removeCriticalField(field)}
                style={{ fontSize:10, padding:'4px 6px', border:`1px solid #dc2626`, borderRadius:12, background:'#dc2626', color:'white', cursor:'pointer' }}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
      
      {/* Text input for manual entry */}
      <input 
        value={criticalFields.join(',')} 
        onChange={e=> setCriticalFields(e.target.value.split(',').map(s=>s.trim()).filter(Boolean))} 
        placeholder="Enter critical fields separated by commas, or use Sync to auto-populate"
        style={{ width:'100%', fontSize:12, padding:'8px 10px', background: inputBg, border:`1px solid ${inputBorder}`, borderRadius:10 }} 
      />
    </div>
  );
};

export default CriticalFieldsEditor;
