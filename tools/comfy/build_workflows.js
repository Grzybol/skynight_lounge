const fs = require("fs");
const path = require("path");

const outputDirectory = path.join(__dirname, "generated");
fs.mkdirSync(outputDirectory, { recursive: true });

const sharedStyle =
  "Match the approved Miners Fortune direction: an original hand-drawn 2D cartoon game icon with bold clean dark ink outlines, simplified appealing shapes, matte gouache texture, controlled cel shading, small hand-painted imperfections, strong silhouette and excellent readability at 200 pixels. Remove glossy 3D rendering, bloom, neon glow, photorealism and excessive highlights. Keep generous padding around the subject. Isolate it on a perfectly flat neutral light-gray background with no shadow, gradient or texture. No border and no extra objects.";

const symbolSpecs = {
  H1: "Transform the supplied miner into a new illustrated older miner with a large white moustache, brown helmet and one round lamp. Preserve the centered front-facing silhouette.",
  H2: "Transform the supplied mine cart into a new illustrated wooden mine cart filled with chunky golden ore. Preserve the front three-quarter view.",
  H3: "Transform the supplied red mining tool into a new illustrated heavy pneumatic mining drill or jackhammer. Preserve its diagonal orientation.",
  H4: "Transform the supplied shovel into a new illustrated miner shovel. Preserve its diagonal orientation, D-shaped handle and broad steel blade.",
  H5: "Transform the supplied pickaxe into a new illustrated miner pickaxe. Preserve its long handle and two-sided steel head.",
  L1: "Transform the supplied red heart gemstone into a new illustrated faceted heart-shaped ruby. Preserve the exact silhouette and red color family.",
  L2: "Transform the supplied purple spade gemstone into a new illustrated faceted spade-shaped amethyst. Preserve the exact silhouette.",
  L3: "Transform the supplied green club gemstone into a new illustrated faceted club-shaped emerald. Preserve the exact silhouette.",
  L4: "Transform the supplied blue diamond gemstone into a new illustrated faceted diamond-shaped aquamarine. Preserve the exact silhouette.",
  W: "Transform the supplied dynamite Wild into a new illustrated bundle of three red dynamite sticks. Keep one readable uppercase W on the badge, exactly W.",
  S: "Transform the supplied Scatter crystal into a new illustrated purple crystal. Keep the word SCATTER exactly in uppercase.",
  M2: "Transform the supplied 2x multiplier into a miner-themed round badge. Keep exactly 2x, large and readable.",
  M4: "Transform the supplied 4x multiplier into a miner-themed round badge. Keep exactly 4x, large and readable.",
  M5: "Transform the supplied 5x multiplier into a miner-themed badge framed by crossed pickaxes. Keep exactly 5x.",
  M7: "Transform the supplied 7x multiplier into a miner-themed badge framed by crossed pickaxes. Keep exactly 7x.",
  M10: "Transform the supplied 10x multiplier into a premium miner-themed badge framed by crossed pickaxes. Keep exactly 10x.",
};

function qwenCore() {
  return {
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
  };
}

function buildSymbolBatch() {
  const prompt = qwenCore();
  let nextNodeId = 10;
  let seed = 9001001;

  for (const [symbol, request] of Object.entries(symbolSpecs)) {
    const loadId = String(nextNodeId++);
    const positiveId = String(nextNodeId++);
    const negativeId = String(nextNodeId++);
    const encodeId = String(nextNodeId++);
    const samplerId = String(nextNodeId++);
    const decodeId = String(nextNodeId++);
    const saveId = String(nextNodeId++);

    prompt[loadId] = {
      class_type: "LoadImage",
      inputs: { image: `${symbol}_original.png` },
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
        filename_prefix: `slot_poc/static_drafts/${symbol}_drawn`,
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
      inputs: { image: "mine_background_source.png" },
    },
    11: {
      class_type: "TextEncodeQwenImageEdit",
      inputs: {
        clip: ["5", 0],
        vae: ["6", 0],
        image: ["10", 0],
        prompt:
          "Transform the supplied underground mine background into an original hand-painted 2D cartoon game backdrop. Preserve the wide composition, tunnel perspective, timber supports, hanging lanterns, mine rails, foreground crystals and clear darker central space reserved for a slot-game board. Use bold clean ink accents, simplified shapes, matte gouache texture, controlled cel shading, subtle paper-brush imperfections, warm amber lantern light against deep plum and indigo rock. No people, text, logo, board, UI, symbols or watermark.",
      },
    },
    12: {
      class_type: "TextEncodeQwenImageEdit",
      inputs: {
        clip: ["5", 0],
        vae: ["6", 0],
        image: ["10", 0],
        prompt:
          "photorealistic, glossy 3D render, neon, text, logo, watermark, people, slot reels, interface",
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
        seed: 74829135,
        steps: 12,
        cfg: 2.5,
        sampler_name: "euler",
        scheduler: "simple",
        positive: ["11", 0],
        negative: ["12", 0],
        latent_image: ["13", 0],
        denoise: 0.86,
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
        filename_prefix: "slot_poc/background_drawn_v1",
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
      inputs: { image: `slot_poc/static_drafts/${symbol}_drawn_00001_.png` },
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
        filename_prefix: `slot_poc/alpha_final/${symbol}_alpha`,
      },
    };
  }
  return { prompt };
}

const workflows = {
  qwen_symbol_batch_api: buildSymbolBatch(),
  qwen_background_api: buildBackground(),
  background_removal_batch_api: buildBackgroundRemoval(),
};

for (const [name, workflow] of Object.entries(workflows)) {
  fs.writeFileSync(
    path.join(outputDirectory, `${name}.json`),
    JSON.stringify(workflow, null, 2),
  );
}

console.log(
  `Wrote ${Object.keys(workflows).length} workflows to ${outputDirectory}`,
);
