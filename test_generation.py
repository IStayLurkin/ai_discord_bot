"""
Test image generation with Diffusers
"""
import torch
from diffusers import StableDiffusionPipeline

print("Testing image generation...")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

# Determine device and dtype
if torch.cuda.is_available():
    device = "cuda"
    dtype = torch.float16
    print("Using CUDA with FP16")
else:
    device = "cpu"
    dtype = torch.float32
    print("Using CPU with FP32")

try:
    print("\nLoading SDXL-Turbo model...")
    # SDXL-Turbo uses StableDiffusionXLPipeline, not StableDiffusionPipeline
    from diffusers import StableDiffusionXLPipeline
    
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=dtype,
        variant="fp16" if device == "cuda" else None
    )
    
    if device == "cuda":
        pipe = pipe.to("cuda")
    else:
        pipe = pipe.to("cpu")
    
    print("Model loaded successfully!")
    
    print("\nGenerating image...")
    prompt = "a cyberpunk lion warrior, ultra detailed"
    # SDXL-Turbo uses guidance_scale=0 and fewer steps
    image = pipe(
        prompt, 
        num_inference_steps=4,
        guidance_scale=0.0
    ).images[0]
    
    output_path = "test.png"
    image.save(output_path)
    
    print(f"\n✅ SUCCESS — Image saved as {output_path}")
    print(f"Prompt: {prompt}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

