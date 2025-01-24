from huggingface_hub import hf_hub_cache_dir

cache_dir = hf_hub_cache_dir()
print(f"Cache directory: {cache_dir}")
