import os
import subprocess
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def extract_and_decompile(jar_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    subprocess.run(["cfr", jar_path, "--outputdir", output_dir])

def translate_to_rust(java_code):
    prompt = f"""
    أنت خبير في لغة Rust وتطوير مودات محرك Horizon-Rust للعبة ماين كرافت.
    قم بتحويل كود مود الجافا التالي إلى كود Rust كامل وصحيح، مع الالتزام الصارم بقواعد الذاكرة (Ownership) في Rust.
    أعطني كود ملف lib.rs فقط بدون أي شرح إضافي أو علامات تنسيق Markdown.

    كود الجافا:
    {java_code}
    """
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
    )
    return response.text.replace("```rust", "").replace("```", "").strip()

if __name__ == "__main__":
    jar_file = "input_mod.jar"
    if os.path.exists(jar_file):
        extract_and_decompile(jar_file, "decompiled_java")
        all_java_code = ""
        for root, _, files in os.walk("decompiled_java"):
            for file in files:
                if file.endswith(".java"):
                    with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                        all_java_code += f"\n// File: {file}\n" + f.read()
        
        rust_code = translate_to_rust(all_java_code[:30000])
        os.makedirs("rust_mod/src", exist_ok=True)
        with open("rust_mod/src/lib.rs", "w", encoding="utf-8") as f:
            f.write(rust_code)
        print("تمت الترجمة بنجاح!")
