<script lang="ts">
	import { t } from '../../game/skyjump/copy';
</script>

<section class="rules">
	<h2>{t('SKYJUMP RULES')}</h2>
	<ol>
		<li>{t('RULE_1')}</li>
		<li>{t('RULE_WEATHER')}</li>
		<li>{t('RULE_2')}</li>
		<li>{t('RULE_3')}</li>
		<li>{t('RULE_4')}</li>
		<li>{t('RULE_5')}</li>
		<li>{t('RULE_6')}</li>
		<li>{t('MODE COST HINT')}</li>
		<li>{t('RULE_7')}</li>
		<li>{t('RULE_8')}</li>
	</ol>
</section>

<style>
	.rules {
		width: min(100%, 720px);
	}

	ol {
		display: grid;
		gap: 0.7rem;
		padding-left: 1.2rem;
		line-height: 1.4;
	}
</style>
