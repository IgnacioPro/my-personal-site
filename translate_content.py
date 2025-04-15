import os
import openai
import frontmatter
from pathlib import Path
import difflib

# Set your target language here
TARGET_LANGUAGE = "es"

openai.api_key = os.environ["OPENAI_API_KEY"]

CONTENT_DIR = Path("content")
TRANSLATED_DIR = CONTENT_DIR / TARGET_LANGUAGE

# Ensure translated directory exists
TRANSLATED_DIR.mkdir(parents=True, exist_ok=True)

def get_changed_files():
    # Use git to get list of changed markdown files in content/
    import subprocess
    result = subprocess.run([
        "git", "diff", "--name-only", "HEAD^", "HEAD", "--", "content/**/*.md"
    ], capture_output=True, text=True)
    files = [f.strip() for f in result.stdout.splitlines() if f.strip() and f.endswith(".md")]
    return files

def translate_text(text, target_language=TARGET_LANGUAGE):
    prompt = f"Translate the following Markdown content to {target_language} (keep YAML frontmatter as-is):\n\n{text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()

def main():
    changed_files = get_changed_files()
    if not changed_files:
        print("No changed markdown files detected.")
        return

    for file_path in changed_files:
        src_path = Path(file_path)
        with open(src_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
        # Only translate the content, not the frontmatter
        translated_content = translate_text(post.content)
        translated_post = frontmatter.Post(translated_content, **post.metadata)
        # Save to translated directory, keeping subfolder structure
        rel_path = src_path.relative_to(CONTENT_DIR)
        target_path = TRANSLATED_DIR / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(translated_post))
        print(f"Translated {src_path} -> {target_path}")

if __name__ == "__main__":
    main()
