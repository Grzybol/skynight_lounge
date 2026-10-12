export const waitForPaint = () =>
	new Promise<void>((resolve) => {
		let done = false;
		const finish = () => {
			if (done) return;
			done = true;
			resolve();
		};
		const failSafe = setTimeout(finish, 50);
		if (typeof requestAnimationFrame !== 'function') {
			clearTimeout(failSafe);
			finish();
			return;
		}
		requestAnimationFrame(() =>
			requestAnimationFrame(() => {
				clearTimeout(failSafe);
				finish();
			}),
		);
	});
