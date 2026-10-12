<script lang="ts" generics="TValue extends string | number">
	import type { Snippet } from 'svelte';

	type Props = {
		value: TValue;
		options: Readonly<TValue[]>;
		onchange: (value: TValue) => void;
		children: Snippet<
			[
				{
					disabledDown: boolean;
					disabledUp: boolean;
					toggleDown: () => any;
					toggleUp: () => any;
				},
			]
		>;
	};

	const props: Props = $props();

	// The current value may sit between options (a capped or zero bet), so look for
	// the nearest option on each side instead of trusting an exact index.
	const smaller = $derived(
		[...props.options].reverse().find((option) => option < props.value),
	);
	const bigger = $derived(props.options.find((option) => option > props.value));
	const disabledDown = $derived(smaller === undefined);
	const disabledUp = $derived(bigger === undefined);

	const toggleDown = () => {
		if (smaller !== undefined) props.onchange(smaller);
	};
	const toggleUp = () => {
		if (bigger !== undefined) props.onchange(bigger);
	};
</script>

{@render props.children({
	disabledDown,
	disabledUp,
	toggleDown,
	toggleUp,
})}
