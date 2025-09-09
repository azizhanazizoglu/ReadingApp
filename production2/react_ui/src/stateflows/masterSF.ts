import { runFindHomePageSF } from "./findHomePageSF";

export type SFResult = {
  ok: boolean;
  changed?: boolean;
  reason?: string;
  data?: any;
};

export type SFRunner = (opts?: { log?: (msg: string) => void }) => Promise<SFResult>;

export type MasterStep = {
  name: string;
  run: SFRunner;
  // Control flags: keep it simple; expand later if needed
  stopOnChanged?: boolean; // default true
};

export async function runMasterSF(steps?: MasterStep[], opts?: { log?: (msg: string) => void }) {
  const log = opts?.log || (() => {});
  const plan: MasterStep[] = steps && steps.length ? steps : [
    { name: "findHomePage", run: ({ log }) => runFindHomePageSF({ log }), stopOnChanged: true },
    // Add more features here later, e.g. fillFormSF, readOCRSF, etc.
  ];

  const results: { name: string; result: SFResult }[] = [];
  for (const step of plan) {
    log(`[MasterSF] start: ${step.name}`);
    const res = await step.run({ log: (m) => log(`[${step.name}] ${m}`) });
    results.push({ name: step.name, result: res });
    log(`[MasterSF] done: ${step.name} -> ok=${res.ok} changed=${!!res.changed} reason=${res.reason || ""}`);
    const stopOnChanged = step.stopOnChanged !== false;
    if (stopOnChanged && res.changed) {
      log(`[MasterSF] stopping on changed at ${step.name}`);
      return { ok: true, stoppedAt: step.name, results };
    }
  }
  return { ok: true, stoppedAt: null as string | null, results };
}

// Convenience exports for callers to build their own plans
export const FeatureSF = {
  findHomePage: (opts?: { log?: (msg: string) => void }) => runFindHomePageSF(opts),
  // fillForm: ... (future)
  // readOCR: ... (future)
};
