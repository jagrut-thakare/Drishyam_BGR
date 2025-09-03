from diffusers import AutoPipelineForInpainting, AutoencoderKL
from PIL import Image, ImageOps, ImageFilter
import torch, numpy as np

# === Load a better, fine-tuned VAE ===
print("🔧 Loading fine-tuned VAE...")
vae = AutoencoderKL.from_pretrained(
    "madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16
)

print("✅ Loaded fp16-fix VAE.")


# === Initialize SDXL inpainting pipeline WITH the custom VAE ===
print("🔧 Loading inpainting pipeline with custom VAE...")

pipe = AutoPipelineForInpainting.from_pretrained(
    "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
    vae=vae, torch_dtype=torch.float16, variant="fp16"
).to("cuda")
pipe.enable_attention_slicing()

print("✔️ Pipeline loaded. Preparing image with noise...")


def run_inpainting(input_path, mask_path, output_path, prompt):
    image_input = Image.open(input_path).convert("RGB")
    mask_image = Image.open(mask_path).convert("L")
    w, h = image_input.size
    max_dim = max(w, h)
    pad_w = (max_dim - w) // 2
    pad_h = (max_dim - h) // 2

    avg_color = np.array(image_input).mean(axis=(0, 1)).astype(int)
    fill_color = tuple(avg_color)

    image_padded = ImageOps.expand(
        image_input, (pad_w, pad_h, max_dim - w - pad_w, max_dim - h - pad_h),
        fill=fill_color
    ).resize((1024, 1024), Image.BICUBIC)   # resample , can be added

    mask_padded = ImageOps.expand(
        mask_image, (pad_w, pad_h, max_dim - w - pad_w, max_dim - h - pad_h),
        fill=0
    ).resize((1024, 1024), Image.BICUBIC).filter(ImageFilter.GaussianBlur(8))   # radius can be added

    image_np = np.array(image_padded)
    mask_np = np.array(mask_padded) > 128

    noise = np.random.normal(loc=0, scale=18, size=image_np.shape).astype(np.int16)
    original_pixels = image_np[mask_np].astype(np.int16)
    blended = np.clip(original_pixels + noise[mask_np], 0, 255).astype(np.uint8)
    image_np[mask_np] = blended
    image_noisy = Image.fromarray(image_np)
    image_noisy.save("../input_with_noise_blended.png")

    result = pipe(
        prompt=prompt,
        negative_prompt="painting, ugly, watermark, text, signature, deformed,  disfigured, poor anatomy, bad lighting, visible seam, blurry, low resolution, logo",
        image=image_noisy,
        mask_image=mask_padded,
        strength=0.95,
        guidance_scale=8.5,
        num_inference_steps=30,
        generator=torch.Generator(device="cuda").manual_seed(69),
    )
    result_img = result.images[0]
    unpadded = result_img.crop((
        pad_w * result_img.width // max_dim,
        pad_h * result_img.height // max_dim,
        (pad_w + w) * result_img.width // max_dim,
        (pad_h + h) * result_img.height // max_dim,
    ))
    final = unpadded.resize((w, h), Image.LANCZOS)  #resample add?
    final.save(output_path)

    print("✅ Inpainting complete!")
