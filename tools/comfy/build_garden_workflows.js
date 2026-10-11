const fs = require("fs");
const path = require("path");

const outputDirectory = path.join(__dirname, "generated");
fs.mkdirSync(outputDirectory, { recursive: true });

const sharedStyle =
  "Match the approved hand-drawn slot-game direction: an original 2D cartoon garden icon with bold clean dark ink outlines, simplified appealing shapes, matte gouache texture, controlled cel shading, small hand-painted imperfections, strong silhouette and excellent readability at 200 pixels. Use a warm harvest palette with leafy greens, tomato red, aubergine purple, blueberry blue, sunflower yellow and natural wood. Remove glossy 3D rendering, bloom, neon glow, photorealism and excessive highlights. Keep generous padding around the subject. Isolate it on a perfectly flat neutral light-gray background with no shadow, gradient or texture. No border and no extra objects.";

const symbolSpecs = {
  H1: "Transform the supplied miner into a friendly older gardener with a large white moustache, straw hat and green work shirt. Preserve the centered front-facing head-and-shoulders silhouette.",
  H2: "Transform the supplied mine cart into a wooden garden wheelbarrow filled with tomatoes, carrots and leafy vegetables. Preserve the compact front three-quarter silhouette.",
  H3: "Transform the supplied mining drill into a charming rounded metal watering can with a curved handle and long spout. Preserve the strong diagonal orientation.",
  L1: "Transform the supplied red gemstone into a plump ripe red tomato with one small green leaf crown. Preserve a compact centered silhouette.",
  L2: "Transform the supplied purple gemstone into a painted purple aubergine with a green cap. Preserve a compact centered silhouette.",
  L3: "Transform the supplied green gemstone into a bright green broccoli crown with a short stalk. Preserve a compact centered silhouette.",
  L4: "Transform the supplied blue gemstone into a cluster of three deep-blue blueberries with two green leaves. Preserve a compact centered silhouette.",
  W: "Transform the supplied Wild dynamite into crossed garden shears behind a sunflower and a small wooden badge. Keep exactly one large readable uppercase W on the badge.",
  S: "Transform the supplied Scatter crystal into a premium golden pumpkin with curling green vines. Keep the word SCATTER exactly in uppercase and clearly readable.",
  M2: "Transform the supplied 2x multiplier into a round painted wooden garden badge framed by small leaves. Keep exactly 2x, large and readable.",
  M4: "Transform the supplied 4x multiplier into a round painted wooden garden badge framed by small leaves. Keep exactly 4x, large and readable.",
  M5: "Transform the supplied 5x multiplier into a premium garden badge framed by tomatoes, leaves and tiny flowers. Keep exactly 5x, large and readable.",
  M7: "Transform the supplied 7x multiplier into a premium garden badge framed by aubergines, leaves and tiny flowers. Keep exactly 7x, large and readable.",
  M10: "Transform the supplied 10x multiplier into a premium harvest badge framed by a rich wreath of vegetables, leaves and sunflowers. Keep exactly 10x, large and readable.",
};

const qwenCore = () => ({
  1: {
    class_type: "UNETLoader",
    inputs: {
      unet_name: "qwen_image_edit_fp8_e4m3fn.safetensors",
      weight_dtype: "default",
    },
  },
  2: {
    class_type: "LoraLoaderModelOnly",
    inputs: {
      model: ["1", 0],
      lora_name: "Qwen-Image-Lightning-4steps-V1.0.safetensors",
      strength_model: 1,
    },
  },
  3: {
    class_type: "ModelSamplingAuraFlow",
    inputs: { model: ["2", 0], shift: 3 },
  },
  4: {
    class_type: "CFGNorm",
    inputs: { model: ["3", 0], strength: 1 },
  },
  5: {
    class_type: "CLIPLoader",
    inputs: {
      clip_name: "qwen_2.5_vl_7b_fp8_scaled.safetensors",
      type: "qwen_image",
      device: "default",
    },
  },
  6: {
    class_type: "VAELoader",
    inputs: { vae_name: "qwen_image_vae.safetensors" },
  },
});

function buildSymbolBatch() {
  const prompt = qwenCore();
  let nodeId = 10;
  let seed = 9302001;

  for (const [symbol, request] of Object.entries(symbolSpecs)) {
    const loadId = String(nodeId++);
    const positiveId = String(nodeId++);
    const negativeId = String(nodeId++);
    const encodeId = String(nodeId++);
    const samplerId = String(nodeId++);
    const decodeId = String(nodeId++);
    const saveId = String(nodeId++);

    prompt[loadId] = {
      class_type: "LoadImage",
      inputs: { image: `garden_${symbol}_source.png` },
    };
    prompt[positiveId] = {
      class_type: "TextEncodeQwenImageEdit",
      inputs: {
        clip: ["5", 0],
        vae: ["6", 0],
        image: [loadId, 0],
        prompt: `${request} ${sharedStyle}`,
      },
    };
    prompt[negativeId] = {
      class_type: "TextEncodeQwenImageEdit",
      inputs: { clip: ["5", 0], vae: ["6", 0], image: [loadId, 0], prompt: "" },
    };
    prompt[encodeId] = {
      class_type: "VAEEncode",
      inputs: { pixels: [loadId, 0], vae: ["6", 0] },
    };
    prompt[samplerId] = {
      class_type: "KSampler",
      inputs: {
        model: ["4", 0],
        seed: seed++,
        steps: 4,
        cfg: 1,
        sampler_name: "euler",
        scheduler: "simple",
        positive: [positiveId, 0],
        negative: [negativeId, 0],
        latent_image: [encodeId, 0],
        denoise: 1,
      },
    };
    prompt[decodeId] = {
      class_type: "VAEDecode",
      inputs: { samples: [samplerId, 0], vae: ["6", 0] },
    };
    prompt[saveId] = {
      class_type: "SaveImage",
      inputs: {
        images: [decodeId, 0],
        filename_prefix: `slot_garden/static_drafts/${symbol}_drawn`,
      },
    };
  }

  return { prompt };
}

function buildBackground() {
  const prompt = qwenCore();
  Object.assign(prompt, {
    10: {
      class_type: "LoadImage",
      inputs: { image: "garden_background_source.png" },
    },
    11: {
      class_type: "TextEncodeQwenImageEdit",
      inputs: {
        clip: ["5", 0],
        vae: ["6", 0],
        image: ["10", 0],
        prompt:
          "Transform the supplied mine scene into an original hand-painted 2D cartoon garden and orchard backdrop. Preserve the wide composition, strong framing, depth, and clear darker central space reserved for a slot-game board. Replace rock walls with leafy fruit trees, flowering hedges, a wooden pergola, raised vegetable beds and a winding stone path. Add warm late-afternoon sunlight, soft blue sky, sunflowers, tomatoes and subtle painted foliage. Use bold clean ink accents, simplified shapes, matte gouache texture, controlled cel shading and small paper-brush imperfections. No people, text, logo, board, UI, symbols or watermark.",
      },
    },
    12: {
      class_type: "TextEncodeQwenImageEdit",
      inputs: {
        clip: ["5", 0],
        vae: ["6", 0],
        image: ["10", 0],
        prompt:
          "mine, underground, cave, rocks, crystals, rails, lanterns, photorealistic, glossy 3D render, neon, text, logo, watermark, people, slot reels, interface",
      },
    },
    13: {
      class_type: "VAEEncode",
      inputs: { pixels: ["10", 0], vae: ["6", 0] },
    },
    14: {
      class_type: "KSampler",
      inputs: {
        model: ["4", 0],
        seed: 93482711,
        steps: 12,
        cfg: 2.5,
        sampler_name: "euler",
        scheduler: "simple",
        positive: ["11", 0],
        negative: ["12", 0],
        latent_image: ["13", 0],
        denoise: 0.92,
      },
    },
    15: {
      class_type: "VAEDecode",
      inputs: { samples: ["14", 0], vae: ["6", 0] },
    },
    16: {
      class_type: "SaveImage",
      inputs: {
        images: ["15", 0],
        filename_prefix: "slot_garden/background_drawn_v1",
      },
    },
  });
  return { prompt };
}

function buildBackgroundRemoval() {
  const prompt = {
    1: {
      class_type: "LoadBackgroundRemovalModel",
      inputs: { bg_removal_name: "birefnet.safetensors" },
    },
  };
  let nodeId = 10;

  for (const symbol of Object.keys(symbolSpecs)) {
    const loadId = String(nodeId++);
    const removeId = String(nodeId++);
    const invertId = String(nodeId++);
    const joinId = String(nodeId++);
    const saveId = String(nodeId++);

    prompt[loadId] = {
      class_type: "LoadImage",
      inputs: { image: `slot_garden/static_drafts/${symbol}_drawn_00001_.png` },
    };
    prompt[removeId] = {
      class_type: "RemoveBackground",
      inputs: { bg_removal_model: ["1", 0], image: [loadId, 0] },
    };
    prompt[invertId] = {
      class_type: "InvertMask",
      inputs: { mask: [removeId, 0] },
    };
    prompt[joinId] = {
      class_type: "JoinImageWithAlpha",
      inputs: { image: [loadId, 0], alpha: [invertId, 0] },
    };
    prompt[saveId] = {
      class_type: "SaveImage",
      inputs: {
        images: [joinId, 0],
        filename_prefix: `slot_garden/alpha_final/${symbol}_alpha`,
      },
    };
  }
  return { prompt };
}

function buildH1HatFix() {
  const prompt = qwenCore();
  const request =
    "Keep this exact same friendly older gardener: same face, white moustache, white beard, green work shirt and brown suspenders. Finish the straw hat as a plain farmer hat. The crown is smooth continuous straw felt with only a dark brown hat band. Remove leftover paint patches, circular dents, lamp outlines, gold discs and miner headlamps. Preserve the centered front-facing head-and-shoulders silhouette.";
  Object.assign(prompt, {
    10: {
      class_type: "LoadImage",
      inputs: { image: "garden_H1_hatfix_source.png" },
    },
    11: {
      class_type: "TextEncodeQwenImageEdit",
      inputs: {
        clip: ["5", 0],
        vae: ["6", 0],
        image: ["10", 0],
        prompt: `${request} ${sharedStyle}`,
      },
    },
    12: {
      class_type: "TextEncodeQwenImageEdit",
      inputs: {
        clip: ["5", 0],
        vae: ["6", 0],
        image: ["10", 0],
        prompt:
          "miner headlamp, headlight, gold circle, circular badge, lamp housing, flashlight, dent, oval patch, miner helmet, glossy 3D, photorealism, extra objects, text, watermark",
      },
    },
    13: {
      class_type: "VAEEncode",
      inputs: { pixels: ["10", 0], vae: ["6", 0] },
    },
    14: {
      class_type: "KSampler",
      inputs: {
        model: ["4", 0],
        seed: 9302105,
        steps: 4,
        cfg: 1,
        sampler_name: "euler",
        scheduler: "simple",
        positive: ["11", 0],
        negative: ["12", 0],
        latent_image: ["13", 0],
        denoise: 0.7,
      },
    },
    15: {
      class_type: "VAEDecode",
      inputs: { samples: ["14", 0], vae: ["6", 0] },
    },
    16: {
      class_type: "SaveImage",
      inputs: {
        images: ["15", 0],
        filename_prefix: "slot_garden/static_drafts/H1_hatfix",
      },
    },
  });
  return { prompt };
}

function buildH1HatFixAlpha() {
  return {
    prompt: {
      1: {
        class_type: "LoadBackgroundRemovalModel",
        inputs: { bg_removal_name: "birefnet.safetensors" },
      },
      10: {
        class_type: "LoadImage",
        inputs: { image: "slot_garden/static_drafts/H1_hatfix_00002_.png" },
      },
      11: {
        class_type: "RemoveBackground",
        inputs: { bg_removal_model: ["1", 0], image: ["10", 0] },
      },
      12: {
        class_type: "InvertMask",
        inputs: { mask: ["11", 0] },
      },
      13: {
        class_type: "JoinImageWithAlpha",
        inputs: { image: ["10", 0], alpha: ["12", 0] },
      },
      14: {
        class_type: "SaveImage",
        inputs: {
          images: ["13", 0],
          filename_prefix: "slot_garden/alpha_final/H1_alpha",
        },
      },
    },
  };
}

const workflows = {
  garden_symbol_batch_api: buildSymbolBatch(),
  garden_background_api: buildBackground(),
  garden_background_removal_batch_api: buildBackgroundRemoval(),
  garden_h1_hat_fix_api: buildH1HatFix(),
  garden_h1_hat_fix_alpha_api: buildH1HatFixAlpha(),
};

for (const [name, workflow] of Object.entries(workflows)) {
  fs.writeFileSync(
    path.join(outputDirectory, `${name}.json`),
    JSON.stringify(workflow, null, 2),
  );
}

console.log(
  `Wrote ${Object.keys(workflows).length} garden workflows to ${outputDirectory}`,
);
