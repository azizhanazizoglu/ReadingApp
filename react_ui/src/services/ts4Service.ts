import { runTs2 } from './ts2Service';
import { runTs3 } from './ts3Service';

export type Ts4Options = {
  highlight?: boolean;
  stepDelayMs?: number;
  simulateTyping?: boolean;
  useDummyWhenEmpty?: boolean;
  useBackendScript?: boolean;
};

export async function runTs4(backEndUrl: string, devLog?: (c: string, m: string) => void, opts?: Ts4Options) {
  devLog?.('IDX-TS4-START', 'TS4: TS2 + TS3 (next page)');
  const ts2 = await runTs2(backEndUrl, undefined, devLog);
  devLog?.('IDX-TS4-TS2', JSON.stringify({ mappingSavedTo: ts2?.path, htmlSavedTo: ts2?.html_saved_to || '' }));
  const ts3 = await runTs3(backEndUrl, devLog, {
    highlight: opts?.highlight,
    stepDelayMs: opts?.stepDelayMs,
    simulateTyping: opts?.simulateTyping,
    useDummyWhenEmpty: opts?.useDummyWhenEmpty,
    useBackendScript: opts?.useBackendScript,
  });
  devLog?.('IDX-TS4-DONE', 'TS4 tamamlandı');
  return { ts2, ts3 };
}
