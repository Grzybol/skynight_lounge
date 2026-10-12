/**
 * Player-facing wording for the summary tile under the slot.
 *
 * The book handlers still build their labels from the original engine vocabulary (rejump,
 * judge, thermal, flight ...). This maps them to Midnight Lounge words and drops debug detail
 * (limits, flags, counters), so nothing from the old ski-jumping game or the engine reaches the
 * player. Pure functions, unit tested in tools/midnight-lounge/test-status-text.ts.
 */

const LABEL_RULES: Array<[RegExp, string]> = [
	[/^REJUMP BOARD$/i, 'RESPIN'],
	[/^REJUMP (\d+) (?:DONE|SKIPPED)$/i, 'RESPIN $1'],
	[/^REJUMP (\d+) LINES$/i, 'RESPIN $1'],
	[/^REJUMP (\d+)\s*·\s*/i, 'RESPIN $1 · '],
	[/^REJUMP (\d+)$/i, 'RESPIN $1'],
	[/^SNOWBURST$/i, 'MYSTERY GIFTS'],
	[/^COACH SIGNAL$/i, 'CONCIERGE'],
	[/^COACH$/i, 'CONCIERGE'],
	[/^GATE UPGRADE$/i, 'VIP UPGRADE'],
	[/^THERMAL$/i, 'GOLDEN SPOTLIGHT'],
	[/^JUDGE COLLECT$/i, 'DEALER COLLECTS'],
	[/^HEAD JUDGE$/i, 'PIT BOSS COLLECTS'],
	[/^PERSISTENT TARGET$/i, 'MYSTERY TARGET'],
	[/^CAPPED TOTAL$/i, 'MAX WIN'],
	[/^MAX WIN · TERMINATED$/i, 'MAX WIN'],
	[/^MAX WIN CAP$/i, 'MAX WIN'],
	[/^ACCESS PASS · (?:CHARGE|UPGRADE)$/i, 'BLACK ACCESS PASS'],
	[/^ACCESS PASS$/i, 'BLACK ACCESS PASS'],
];

/** Sub-line segments (split on " · ") that are engine/debug detail and never shown. */
const DROP_SEGMENT = /terminated|truncated|drag|FS cancelled|cancelled|redrop|keep \d|spin #|MAX_|_PER_|no effect|may pick|unchanged|updated|^limit$/i;

const WORD_RULES: Array<[RegExp, string]> = [
	[/\bflight\b/gi, 'lounge'],
	[/\bjudge\b/gi, 'dealer'],
	[/\bthermal\b/gi, 'spotlight'],
	[/\bgate\b/gi, 'upgrade'],
	[/\bcoach\b/gi, 'concierge'],
	[/\brejump\b/gi, 'respin'],
	[/\bsnow\w*/gi, 'gift'],
	[/\bski\b/gi, ''],
	[/\bhill\b/gi, 'room'],
];

export const statusLabel = (label: string): string => {
	let out = label.trim();
	for (const [re, to] of LABEL_RULES) {
		if (re.test(out)) {
			out = out.replace(re, to);
			break;
		}
	}
	for (const [re, to] of WORD_RULES) out = out.replace(re, to);
	return out.replace(/\s{2,}/g, ' ').trim();
};

export const statusSub = (sub: string): string => {
	if (!sub) return '';
	const parts = sub
		.split(' · ')
		.map((p) => p.trim())
		.filter((p) => p && !DROP_SEGMENT.test(p));
	let out = parts.join(' · ');
	// "2.5x · L3" -> "2.5x · line 3"
	out = out.replace(/\bL(\d+)\b/g, 'line $1');
	// "+12.0x → 50.0x" keeps only the capped figure for max wins.
	for (const [re, to] of WORD_RULES) out = out.replace(re, to);
	return out.replace(/\s{2,}/g, ' ').trim();
};
