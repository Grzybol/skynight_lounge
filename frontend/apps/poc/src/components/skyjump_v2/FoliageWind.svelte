<script lang="ts">
	import { onMount } from 'svelte';

	/**
	 * A picture drawn with WebGL so its foliage (leaves, stems, roses) can sway in the wind. The art is sampled through a small
	 * animated displacement; a mask (white = foliage, black = stone / metal) keeps everything else perfectly still. Until the first
	 * frame is drawn (and whenever WebGL2 is missing or motion is reduced) the plain image is shown instead.
	 * `left`, `top`, `width`, `height` are CSS px inside the parent; `artW` x `artH` is the size of the texture in art px
	 * (the displacement is `amplitude` art px).
	 */
	type Props = {
		src: string;
		maskSrc: string;
		left?: number;
		top?: number;
		width: number;
		height: number;
		artW: number;
		artH: number;
		amplitude?: number;
		testId?: string;
	};

	const { src, maskSrc, left = 0, top = 0, width, height, artW, artH, amplitude = 1.5, testId }: Props = $props();

	let canvas = $state<HTMLCanvasElement | null>(null);
	let ready = $state(false);

	const dpr = () => Math.min(2, typeof window === 'undefined' ? 1 : window.devicePixelRatio || 1);

	$effect(() => {
		if (!canvas) return;
		canvas.width = Math.max(2, Math.round(width * dpr()));
		canvas.height = Math.max(2, Math.round(height * dpr()));
	});

	const VERTEX = `#version 300 es
in vec2 aPos;
out vec2 vUv;
void main() {
	vUv = vec2(aPos.x * 0.5 + 0.5, 0.5 - aPos.y * 0.5);
	gl_Position = vec4(aPos, 0.0, 1.0);
}`;

	const FRAGMENT = `#version 300 es
precision highp float;
uniform sampler2D uFrame;
uniform sampler2D uMask;
uniform float uTime;
uniform vec2 uArt;
uniform float uAmp;
in vec2 vUv;
out vec4 outColor;
void main() {
	vec2 p = vUv * uArt;
	float m = texture(uMask, vUv).r;
	float t = uTime;
	// Two slow, wide waves at different scales (half the speed and the frequency of the first version).
	vec2 w = vec2(
		sin(t * 0.95 + p.x * 0.0225 + p.y * 0.0155) + 0.6 * sin(t * 1.55 + p.y * 0.035 - p.x * 0.01),
		cos(t * 0.75 + p.y * 0.02 - p.x * 0.014) + 0.6 * sin(t * 1.3 + p.x * 0.03 + p.y * 0.025)
	);
	vec2 off = w * m * uAmp / uArt;
	outColor = texture(uFrame, vUv + off);
}`;

	const loadImage = (url: string) =>
		new Promise<HTMLImageElement>((resolve, reject) => {
			const img = new Image();
			img.crossOrigin = 'anonymous';
			img.onload = () => resolve(img);
			img.onerror = reject;
			img.src = url;
		});

	onMount(() => {
		if (!canvas) return;
		if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
		const gl = canvas.getContext('webgl2', {
			alpha: true,
			premultipliedAlpha: true,
			antialias: false,
			preserveDrawingBuffer: false,
		});
		if (!gl) return;

		let stopped = false;
		let raf = 0;
		let program: WebGLProgram | null = null;
		const textures: WebGLTexture[] = [];

		const compile = (type: number, source: string) => {
			const shader = gl.createShader(type)!;
			gl.shaderSource(shader, source);
			gl.compileShader(shader);
			if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader) ?? 'shader');
			return shader;
		};

		const upload = (img: HTMLImageElement, unit: number, premultiply: boolean) => {
			const tex = gl.createTexture()!;
			textures.push(tex);
			gl.activeTexture(gl.TEXTURE0 + unit);
			gl.bindTexture(gl.TEXTURE_2D, tex);
			gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, premultiply);
			gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
			gl.generateMipmap(gl.TEXTURE_2D);
			gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
			gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
			gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
			gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
		};

		const start = async () => {
			try {
				const [frame, mask] = await Promise.all([loadImage(src), loadImage(maskSrc)]);
				if (stopped) return;
				program = gl.createProgram()!;
				gl.attachShader(program, compile(gl.VERTEX_SHADER, VERTEX));
				gl.attachShader(program, compile(gl.FRAGMENT_SHADER, FRAGMENT));
				gl.linkProgram(program);
				if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error('link');
				gl.useProgram(program);

				const buffer = gl.createBuffer();
				gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
				gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
				const loc = gl.getAttribLocation(program, 'aPos');
				gl.enableVertexAttribArray(loc);
				gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

				upload(frame, 0, true);
				upload(mask, 1, false);
				gl.uniform1i(gl.getUniformLocation(program, 'uFrame'), 0);
				gl.uniform1i(gl.getUniformLocation(program, 'uMask'), 1);
				gl.uniform2f(gl.getUniformLocation(program, 'uArt'), artW, artH);
				gl.uniform1f(gl.getUniformLocation(program, 'uAmp'), amplitude);
				const uTime = gl.getUniformLocation(program, 'uTime');
				gl.enable(gl.BLEND);
				gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);

				const frameLoop = (now: number) => {
					if (stopped) return;
					raf = requestAnimationFrame(frameLoop);
					if (document.hidden || !canvas) return;
					gl.viewport(0, 0, canvas.width, canvas.height);
					gl.clearColor(0, 0, 0, 0);
					gl.clear(gl.COLOR_BUFFER_BIT);
					gl.uniform1f(uTime, now / 1000);
					gl.drawArrays(gl.TRIANGLES, 0, 3);
					if (!ready) ready = true;
				};
				raf = requestAnimationFrame(frameLoop);
			} catch {
				// Keep the static image layer.
			}
		};
		void start();

		return () => {
			stopped = true;
			cancelAnimationFrame(raf);
			for (const tex of textures) gl.deleteTexture(tex);
			if (program) gl.deleteProgram(program);
			gl.getExtension('WEBGL_lose_context')?.loseContext();
		};
	});
</script>

<div
	class="frame-wind"
	style:left={`${left}px`}
	style:top={`${top}px`}
	style:width={`${width}px`}
	style:height={`${height}px`}
	data-test={testId}
	aria-hidden="true"
>
	{#if !ready}
		<img class="frame-still" {src} alt="" draggable="false" />
	{/if}
	<canvas bind:this={canvas} class="frame-canvas" class:ready></canvas>
</div>

<style>
	.frame-wind {
		position: absolute;
		pointer-events: none;
		user-select: none;
	}

	.frame-still {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		max-width: none;
		object-fit: fill;
	}

	/* Beats Game.svelte's `.skyjump-viewport canvas { position: relative; z-index: 19 }`. */
	:global(.skyjump-viewport canvas.frame-canvas.frame-canvas) {
		position: absolute;
		inset: 0;
		z-index: auto;
		width: 100%;
		height: 100%;
		opacity: 0;
		pointer-events: none;
	}

	:global(.skyjump-viewport canvas.frame-canvas.frame-canvas.ready) {
		opacity: 1;
	}
</style>
