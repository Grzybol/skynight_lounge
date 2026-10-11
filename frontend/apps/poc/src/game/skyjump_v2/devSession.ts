/** DEV-only fixture picker. Production must never import this module. */
export const V2_FIXTURE_SESSION_KEY = 'skyjumpV2Fixture';

export const readDevFixtureSelection = (search = '') => {
	const params = new URLSearchParams(search.startsWith('?') ? search : `?${search}`);
	const fromQuery = params.get('fixture') ?? params.get('v2Fixture');
	if (fromQuery) return fromQuery;
	if (typeof sessionStorage === 'undefined') return null;
	return sessionStorage.getItem(V2_FIXTURE_SESSION_KEY);
};

export const writeDevFixtureSelection = (id: string | null) => {
	if (typeof sessionStorage === 'undefined') return;
	if (!id) {
		sessionStorage.removeItem(V2_FIXTURE_SESSION_KEY);
		return;
	}
	sessionStorage.setItem(V2_FIXTURE_SESSION_KEY, id);
};
