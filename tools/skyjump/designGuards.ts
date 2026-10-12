/**
 * Developer mathVersion 3 design guards. Not runtime / not certification.
 */
import { publishedModes } from './exactEv.ts';
import { auditMode } from './mathAudit.ts';

const warn = (message: string, extra?: unknown) => {
	console.warn(`MATH DESIGN WARN: ${message}`, extra ?? '');
};

const fail = (message: string, extra?: unknown) => {
	throw new Error(`MATH DESIGN FAIL: ${message}${extra ? ` ${JSON.stringify(extra)}` : ''}`);
};

export const runDesignGuards = () => {
	const rows = publishedModes().map(auditMode);
	const byKey = Object.fromEntries(rows.map((row) => [row.rgsKey, row]));
	const base = byKey.BASE;
	const large = byKey.LARGE_HILL;
	const flying = byKey.SKI_FLYING;

	for (const row of rows) {
		if (row.rtp < 0.96 || row.rtp > 0.98) {
			fail(`${row.rgsKey} RTP outside 0.96–0.98`, { rtp: row.rtp });
		}
		if (row.rtp < 0.968 || row.rtp > 0.972) {
			warn(`${row.rgsKey} RTP outside preferred 0.968–0.972`, { rtp: row.rtp });
		}
		if (row.locals.any > 0.28) {
			fail(`${row.rgsKey} any-local frequency too high`, { any: row.locals.any });
		} else if (row.locals.any > 0.22) {
			warn(`${row.rgsKey} any-local above 20% target`, { any: row.locals.any });
		}
		if (row.capDragShareOfRaw > 0.02) {
			fail(`${row.rgsKey} cap drag too high`, { drag: row.capDragShareOfRaw });
		} else if (row.capDragShareOfRaw > 0.01) {
			warn(`${row.rgsKey} cap drag above 1% raw EV`, { drag: row.capDragShareOfRaw });
		}
		const weatherRtps = Object.values(row.weather).map((weather) => weather.conditionalRtp);
		const weatherHits = Object.values(row.weather).map((weather) => weather.hitRate);
		const spread = Math.max(...weatherRtps) / Math.min(...weatherRtps);
		const hitSpread = Math.max(...weatherHits) - Math.min(...weatherHits);
		if (spread > 2.0) fail(`${row.rgsKey} weather RTP spread too large`, { spread });
		else if (spread > 1.6) warn(`${row.rgsKey} weather RTP spread above 1.6`, { spread });
		if (hitSpread > 0.16) fail(`${row.rgsKey} weather hit spread too large`, { hitSpread });
		else if (hitSpread > 0.12) warn(`${row.rgsKey} weather hit spread above 12pp`, { hitSpread });
		if (row.rgsKey === 'BASE' && row.shapleyNominal.subsets.vD < 0.43) {
			warn('BASE distance-only EV below 0.43', { vD: row.shapleyNominal.subsets.vD });
		}
	}

	const cvTol = 0.03;
	if (large.wagerMoments.cv + cvTol < base.wagerMoments.cv) {
		fail('LARGE CV is below BASE', {
			base: base.wagerMoments.cv,
			large: large.wagerMoments.cv,
		});
	} else if (large.wagerMoments.cv < base.wagerMoments.cv) {
		warn('LARGE CV is slightly below BASE', {
			base: base.wagerMoments.cv,
			large: large.wagerMoments.cv,
		});
	}
	if (flying.wagerMoments.cv + cvTol < large.wagerMoments.cv) {
		fail('FLYING CV is below LARGE', {
			large: large.wagerMoments.cv,
			flying: flying.wagerMoments.cv,
		});
	} else if (flying.wagerMoments.cv < large.wagerMoments.cv) {
		warn('FLYING CV is slightly below LARGE', {
			large: large.wagerMoments.cv,
			flying: flying.wagerMoments.cv,
		});
	}

	const pTol = 0.08;
	if (large.percentilesVsWager.p99_9 * (1 + pTol) < base.percentilesVsWager.p99_9) {
		fail('LARGE p99.9 is below BASE', {
			base: base.percentilesVsWager.p99_9,
			large: large.percentilesVsWager.p99_9,
		});
	} else if (large.percentilesVsWager.p99_9 < base.percentilesVsWager.p99_9) {
		warn('LARGE p99.9 is slightly below BASE', {
			base: base.percentilesVsWager.p99_9,
			large: large.percentilesVsWager.p99_9,
		});
	}
	if (flying.percentilesVsWager.p99_9 * (1 + pTol) < large.percentilesVsWager.p99_9) {
		fail('FLYING p99.9 is below LARGE', {
			large: large.percentilesVsWager.p99_9,
			flying: flying.percentilesVsWager.p99_9,
		});
	} else if (flying.percentilesVsWager.p99_9 <= large.percentilesVsWager.p99_9) {
		warn('FLYING p99.9 is not above LARGE', {
			large: large.percentilesVsWager.p99_9,
			flying: flying.percentilesVsWager.p99_9,
		});
	}
	if (flying.tailVsWager.gt50 <= large.tailVsWager.gt50) {
		warn('FLYING P(>50x) is not above LARGE', {
			large: large.tailVsWager.gt50,
			flying: flying.tailVsWager.gt50,
		});
	}

	return rows;
};

if (process.argv[1] && /designGuards\.ts$/i.test(process.argv[1].replaceAll('\\', '/'))) {
	runDesignGuards();
	console.log('skyjump math design guards passed');
}
