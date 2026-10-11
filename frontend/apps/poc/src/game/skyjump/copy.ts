import { stateI18nDerived } from 'state-shared';

export const t = (value: string) => stateI18nDerived.translate(value);
