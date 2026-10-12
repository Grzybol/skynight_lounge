import { i18n, type Messages } from '@lingui/core';
import { type Language } from './stateUrl.svelte';

const LANG_STORAGE_KEY = 'skyjump-lang';

export const stateI18n = $state({
	i18n,
	locale: 'en' as Language,
	catalogs: {} as Partial<Record<Language, Messages>>,
});

const activate = (lang: Language, messages: Messages) => {
	stateI18n.i18n.load(lang, messages);
	stateI18n.i18n.activate(lang);
	stateI18n.locale = lang;
};

export const stateI18nDerived = {
	init: (lang: Language, messages: Messages, catalogs?: Partial<Record<Language, Messages>>) => {
		if (catalogs) stateI18n.catalogs = catalogs;
		activate(lang, messages);
	},
	locale: () => stateI18n.locale,
	switchLanguage: (lang: Language) => {
		const messages = stateI18n.catalogs[lang] || stateI18n.catalogs.en || {};
		activate(lang, messages);
		try {
			localStorage.setItem(LANG_STORAGE_KEY, lang);
		} catch {
			/* ignore */
		}
	},
	storedLanguage: (): Language | null => {
		try {
			const value = localStorage.getItem(LANG_STORAGE_KEY);
			return value === 'en' || value === 'pl' ? value : null;
		} catch {
			return null;
		}
	},
	translate: (value: string) => {
		void stateI18n.locale;
		return stateI18n.i18n._(stateI18n.i18n.t(value));
	},
};
