import { socialize } from 'utils-shared/social';

/** Header artwork with restricted words baked into the pixels: shown as plain text in social mode. */
const BAKED_TITLES: Array<[RegExp, string]> = [
	[/hdr_buy_bonus|ui_buy_bonus_badge/, 'Get bonus'],
	[/ui_header_paytable/, 'Win table'],
];

const ATTRIBUTES = ['aria-label', 'alt', 'title', 'placeholder'] as const;

const fixText = (node: Text) => {
	const value = node.nodeValue ?? '';
	const next = socialize(value);
	if (next !== value) node.nodeValue = next;
};

const fixElement = (el: Element) => {
	for (const name of ATTRIBUTES) {
		const value = el.getAttribute(name);
		if (!value) continue;
		const next = socialize(value);
		if (next !== value) el.setAttribute(name, next);
	}
	if (el instanceof HTMLImageElement && !el.dataset.socialDone) {
		const hit = BAKED_TITLES.find(([re]) => re.test(el.src));
		if (hit) {
			el.dataset.socialDone = '1';
			el.style.display = 'none';
			const label = document.createElement('span');
			label.className = 'social-title';
			label.textContent = hit[1];
			label.setAttribute(
				'style',
				"display:block;text-align:center;color:#f0c75a;font:700 1.7rem/1.2 'Luckiest Guy',Georgia,serif;letter-spacing:.06em;text-transform:uppercase;margin:0 auto;",
			);
			el.insertAdjacentElement('afterend', label);
		}
	}
};

const walk = (root: Node) => {
	if (root.nodeType === Node.TEXT_NODE) return fixText(root as Text);
	if (root.nodeType !== Node.ELEMENT_NODE) return;
	const el = root as Element;
	if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return;
	fixElement(el);
	for (const child of Array.from(el.childNodes)) walk(child);
};

/** `social=true`: rewrites every player-visible HTML string with the restricted-word table (and keeps doing it). */
export const installSocialWording = () => {
	walk(document.body);
	const observer = new MutationObserver((records) => {
		for (const record of records) {
			if (record.type === 'characterData') fixText(record.target as Text);
			else if (record.type === 'attributes') fixElement(record.target as Element);
			else record.addedNodes.forEach((node) => walk(node));
		}
	});
	observer.observe(document.body, {
		subtree: true,
		childList: true,
		characterData: true,
		attributes: true,
		attributeFilter: [...ATTRIBUTES, 'src'],
	});
	return () => observer.disconnect();
};
