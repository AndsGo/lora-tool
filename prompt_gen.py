import os
import torch
from unittest.mock import patch
from transformers.dynamic_module_utils import get_imports
from transformers import AutoModelForCausalLM, AutoProcessor

import comfy.model_management as mm
import folder_paths

model = None
processor = None
attention = 'sdpa'
precision = 'fp16'

device = mm.get_torch_device()
dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[precision]

def fixed_get_imports(filename: str | os.PathLike) -> list[str]:
    if not str(filename).endswith("modeling_florence2.py"):
        return get_imports(filename)
    imports = get_imports(filename)
    try:
        imports.remove("flash_attn")
    except:
        print(f"No flash_attn import to remove")
        pass
    return imports


def tag_image(image, caption_method, max_new_tokens, do_sample, num_beams):
        init("promptgen_large_v2.0")
        if caption_method == 'tags':
            prompt = "<GENERATE_TAGS>"
        elif caption_method == 'simple':
            prompt = "<CAPTION>"
        elif caption_method == 'detailed':
            prompt = "<DETAILED_CAPTION>"
        elif caption_method == 'extra':
            prompt = "<MORE_DETAILED_CAPTION>"
        elif caption_method == 'mixed':
            prompt = "<MIX_CAPTION>"
        elif caption_method == 'extra_mixed':
            prompt = "<MIX_CAPTION_PLUS>"
        else:
            prompt = "<ANALYZE>"

        inputs = processor(text=prompt, images=image, return_tensors="pt", do_rescale=False).to(dtype).to(device)
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=max_new_tokens,
            early_stopping=False,
            do_sample=do_sample,
            num_beams=num_beams,
        )
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_answer = processor.post_process_generation(
            generated_text,
            task=prompt,
            image_size=(image.width, image.height))
        return parsed_answer[prompt]

def init(model_type: str = "promptgen_base_v2.0"):
        global model, processor
        if model is not None and processor is not None:
            return
        # Download model if it does not exist

        hg_model = 'MiaoshouAI/Florence-2-base-PromptGen-v2.0'
        if model_type == 'promptgen_large_v2.0':
            hg_model = 'MiaoshouAI/Florence-2-large-PromptGen-v2.0'
        model_name = hg_model.rsplit('/', 1)[-1]
        model_path = os.path.join(folder_paths.models_dir, "LLM", model_name)
        if not os.path.exists(model_path):
            print(f"Downloading Lumina model to: {model_path}")
            from huggingface_hub import snapshot_download
            snapshot_download(repo_id=hg_model,
                              local_dir=model_path,
                              local_dir_use_symlinks=False)

        with patch("transformers.dynamic_module_utils.get_imports",
                   fixed_get_imports):  # workaround for unnecessary flash_attn requirement
            model = AutoModelForCausalLM.from_pretrained(model_path, attn_implementation=attention, device_map=device,
                                                         torch_dtype=dtype, trust_remote_code=True).to(device)

        # Load the processor
        processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

        