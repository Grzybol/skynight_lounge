<script lang="ts">
	import { zIndex } from 'constants-shared/zIndex';
	import { Popup } from 'components-shared';
	import { stateModal, stateSound } from 'state-shared';

	import BaseTitle from './BaseTitle.svelte';
	import BaseContent from './BaseContent.svelte';
	import BaseScrollable from './BaseScrollable.svelte';
	import ModalSettingsSound from './ModalSettingsSound.svelte';
	import { i18nDerived } from '../i18n/i18nDerived';
</script>

{#if stateModal.modal?.name === 'settings'}
	<Popup zIndex={zIndex.modal} onclose={() => (stateModal.modal = null)}>
		<BaseContent maxWidth="100%">
			<div class="lounge-settings">
			<BaseTitle>{i18nDerived.settings()}</BaseTitle>
			<BaseScrollable type="column">
				<wrap class="wrap">
					<ModalSettingsSound bind:value={stateSound.volumeValueMaster}>
						{i18nDerived.masterVolume()}
					</ModalSettingsSound>

					<ModalSettingsSound bind:value={stateSound.volumeValueMusic}>
						{i18nDerived.musicVolume()}
					</ModalSettingsSound>

					<ModalSettingsSound bind:value={stateSound.volumeValueSoundEffect}>
						{i18nDerived.soundEffectVolume()}
					</ModalSettingsSound>
				</wrap>
			</BaseScrollable>
			</div>
		</BaseContent>
	</Popup>
{/if}

<style lang="scss">
	.lounge-settings {
		box-sizing: border-box;
		width: min(560px, calc(100vw - 48px));
		padding: calc(1.4rem + 22px) calc(1.6rem + 22px) calc(1.6rem + 22px);
		color: #f3e2b8;
		background: none;
		border: 1px solid transparent;
		border-image: var(--ml-panel) 64 fill / 26px stretch;
		filter: drop-shadow(0 18px 28px rgba(0, 0, 0, 0.5));
	}

	.lounge-settings :global(.ui-modal-title-wrap) {
		margin-bottom: 0.8rem;
		color: #f6ead0;
		font-family: var(--skyjump-font-display, 'SkyjumpDisplay', system-ui, sans-serif);
		font-size: 1.15rem;
		font-weight: 800;
		letter-spacing: 0.14em;
		text-transform: uppercase;
	}

	.wrap {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		/* The scroll area clips whatever pokes out on the left (the ON/OFF plates). */
		padding: 0.3rem 0.9rem;
		box-sizing: border-box;

		@media (min-width: 480px) {
			min-width: 360px;
		}

		@media (min-width: 800px) {
			min-width: 480px;
		}
	}
</style>
