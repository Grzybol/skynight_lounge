import { dev } from '$app/environment';
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

/**
 * Bare `/` expects Stake RGS query params (`rgs_url`, `sessionID`).
 * Without them Authenticate fails with TypeError: Failed to fetch.
 * In local DEV, send operators to the live-math harness instead.
 */
export const load: PageLoad = ({ url }) => {
	if (dev && !url.searchParams.get('rgs_url')) {
		throw redirect(302, '/live-preview');
	}
	return {};
};
