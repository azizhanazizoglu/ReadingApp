export async function getTs3Plan(backEndUrl: string, mapping: any, ruhsat_json: any, raw: string, useDummyWhenEmpty: boolean, devLog?: (c: string, m: string) => void) {
  try {
    const r = await fetch(`${backEndUrl}/api/ts3/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mapping, ruhsat_json, raw, options: { use_dummy_when_empty: useDummyWhenEmpty } })
    });
    if (!r.ok) { devLog?.('IDX-TS3-PLAN-ERR', `status ${r.status}`); return { resolved: {}, logs: [] }; }
    const j = await r.json();
    if (Array.isArray(j?.logs)) j.logs.forEach((ln: string, i: number) => devLog?.('IDX-TS3-PLAN', `${i.toString().padStart(3,'0')} ${ln}`));
    if (j?.resolved) devLog?.('IDX-TS3-PLAN-RESOLVED', JSON.stringify(j.resolved));
    return { resolved: j?.resolved || {}, logs: j?.logs || [] };
  } catch (e: any) {
    devLog?.('IDX-TS3-PLAN-ERR', String(e));
    return { resolved: {}, logs: [] };
  }
}
