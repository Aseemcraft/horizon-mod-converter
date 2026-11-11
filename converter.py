import os
import zipfile
import subprocess
import google.generativeai as genai

# إعداد مفتاح Gemini من أسرار المستودع
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-pro')

def extract_and_decompile(jar_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    # تحميل أداة CFR لفك تشفير الجافا مجاناً
    subprocess.run(["wget", "-q", "https://github.com", "-O", "cfr.jar"])
    subprocess.run(["java", "-jar", "cfr.jar", jar_path, "--outputdir", output_dir])

def translate_to_rust(java_code):
    prompt = f"""
    أنت خبير في لغة Rust وتطوير مودات محرك Horizon-Rust للعبة ماين كرافت.
    قم بتحويل كود مود الجافا التالي إلى كود Rust كامل وصحيح، مع الالتزام الصارم بقواعد الذاكرة (Ownership) في Rust.
    أعطني كود ملف lib.rs فقط بدون أي شرح إضافي أو علامات تنسيق Markdown.

    كود الجافا:
    {java_code}
    """
    response = model.generate_content(prompt)
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
        
        rust_code = translate_to_rust(all_java_code[:30000]) # قراءة أول 30 ألف حرف لتجنب تجاوز الحد المجاني
        os.makedirs("rust_mod/src", exist_ok=True)
        with open("rust_mod/src/lib.rs", "w", encoding="utf-8") as f:
            f.write(rust_code)
        print("تمت الترجمة بنجاح!")
