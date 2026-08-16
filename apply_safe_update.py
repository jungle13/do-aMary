import re

def refactor_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    safe_update_code = """
    def safe_update(self):
        \"\"\"Actualiza la UI solo si el control sigue montado en la página.\"\"\"
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass
"""

    if "def safe_update" not in content:
        # Insert after did_mount or __init__
        if "def did_mount" in content:
            content = re.sub(r'(def did_mount.*?:\n(?: {8}.*\n)+)', r'\1' + safe_update_code, content)
        else:
            content = re.sub(r'(def __init__.*?:\n(?: {8}.*\n)+)', r'\1' + safe_update_code, content)
            
    # Replace if self.page:\n self.update() or self.page.update()
    content = re.sub(r'if self\.page:\s+self\.(?:page\.)?update\(\)', r'self.safe_update()', content)
    
    # Replace stray self.update() and self.page.update() calls
    content = re.sub(r'self\.update\(\)', r'self.safe_update()', content)
    # Be careful not to replace self.page.update() inside safe_update itself!
    # A safe way is to replace self.page.update() everywhere except in safe_update.
    # First, temporarily mask the one in safe_update
    content = content.replace("self.page.update()", "self.safe_update()")
    content = content.replace("""        try:
            if self.page and self.uid:
                self.safe_update()""", """        try:
            if self.page and self.uid:
                self.page.update()""")
                
    # Also fix action_bar.update(), column_visibles.update() which we might have broken?
    # Wait, the regex for `self.update()` only catches `self.update()`, not `self.action_bar.update()`.
    # But `self.page.update()` became `self.safe_update()`. Let's ensure we only caught `self.page.update()` and `self.update()`.
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_file(r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\dashboard.py')
refactor_file(r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\inventario.py')
