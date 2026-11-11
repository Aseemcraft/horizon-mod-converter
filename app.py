import os
import zipfile
import subprocess
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def extract_and_decompile(jar_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(jar_path, 'r') as jar:
        jar.extractall(output_dir)
    
    all_java_code = ""
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".class"):
                class_path = os.path.join(root, file)
                result = subprocess.run(["javap", "-c", "-p", class_path], capture_output=True, text=True)
                all_java_code += f"\n// Class: {file}\n" + result.stdout
    return all_java_code

def translate_to_rust(java_code):
    prompt = f"""
    أنت خبير في لغة Rust وتطوير مودات محرك Horizon-Rust للعبة ماين كرافت.
    قم بتحويل كود البايت كود (Bytecode) والكلاسات المستخرجة من مود الجافا التالي إلى كود Rust كامل وصحيح، مع الالتزام الصارم بقواعد الذاكرة (Ownership) في Rust.
    أعطني كود ملف lib.rs فقط بدون أي شرح إضافي أو علامات تنسيق Markdown.

    كود المود المستخرج:
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
        extracted_code = extract_and_decompile(jar_file, "decompiled_java")
        rust_code = translate_to_rust(extracted_code[:30000])
        os.makedirs("rust_mod/src", exist_ok=True)
        with open("rust_mod/src/lib.rs", "w", encoding="utf-8") as f:
            f.write(rust_code)
        print("تمت الترجمة بنجاح!")
