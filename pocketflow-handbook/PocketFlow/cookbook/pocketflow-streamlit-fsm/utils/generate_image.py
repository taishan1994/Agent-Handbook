from openai import OpenAI
import os
import base64

def generate_image(prompt: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    
    image_b64 = response.data[0].b64_json
    print(f"Generated image ({len(image_b64)} chars)")
    return image_b64

if __name__ == "__main__":
    test_prompt = "A gray tabby cat hugging an otter with an orange scarf"
    print(f"Generating image for prompt: {test_prompt[:50]}...")
    
    image_base64 = generate_image(test_prompt)
    print(f"Success! Generated {len(image_base64)} characters of base64 data")
    
    # Write image to local file for testing
    image_bytes = base64.b64decode(image_base64)
    with open("test_generated_image.png", "wb") as f:
        f.write(image_bytes)
    print("Test image saved as test_generated_image.png") 