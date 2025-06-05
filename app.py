import streamlit as st
import requests
import base64
import json
import os
from PIL import Image
import io

class TranslationService:
    def __init__(self, api_key, model, api_url):
        # OpenRouter credentials for translation
        self.translator_key = api_key
        self.translator_url = api_url
        self.model = model

    def translate_image(self, image_bytes):
        try:
            # Convert image bytes to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {self.translator_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful translator that translates text from images between Indonesian and English."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please describe what you see in this image and translate any text you find into both Indonesian and English. Format your response as:\nOriginal: [original text]\nIndonesia: [terjemahan]\nEnglish: [translation]. No need to describe the picture"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(self.translator_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
            return "❌ Error: Failed to process image"

class HistoryManager:
    def __init__(self, filename="history.json"):
        self.filename = filename
        self.history = self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def add_entry(self, filename, result):
        self.history.append({
            "filename": filename,
            "result": result
        })
        self.save()

    def remove_entries(self, indices):
        self.history = [item for i, item in enumerate(self.history) if i not in indices]
        self.save()

    def clear(self):
        self.history = []
        self.save()

    def get_all(self):
        return self.history

class TranslatorApp:
    def __init__(self):
        self.translator = TranslationService(
            api_key="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",
            model="meta-llama/llama-4-maverick",  # Model yang mendukung analisis gambar
            api_url="https://openrouter.ai/api/v1/chat/completions"
        )
        self.history_manager = HistoryManager()

    def run(self):
        st.set_page_config(
            page_title="Document Translator", 
            layout="centered",
            initial_sidebar_state="expanded"
        )
        
        self._display_history()  # Show history in sidebar first
        
        st.title("📷 Text in Image Translation Indonesia-English")
        st.markdown("""
        ### Terjemahkan teks dari gambar ke Bahasa Indonesia dan Inggris.
        """)

        self._handle_image_translation()

    def _handle_image_translation(self):
        st.write("#### 📸 Terjemahan Gambar")
        st.write("Upload gambar yang berisi teks untuk diterjemahkan")
        
        uploaded_file = st.file_uploader(
            "Unggah gambar (JPG, JPEG, PNG)", 
            type=["jpg", "jpeg", "png"]
        )
        
        if uploaded_file:
            image_bytes = uploaded_file.read()
            st.image(image_bytes, caption="Gambar yang diunggah", use_container_width=True)
            
            if st.button("🔄 Terjemahkan Gambar", key="translate_image"):
                with st.spinner("🔍 Menerjemahkan gambar..."):
                    translation = self.translator.translate_image(image_bytes)
                    if not translation.startswith("❌"):  # Only save successful translations
                        self.history_manager.add_entry(uploaded_file.name, translation)
                        st.success("✅ Terjemahan berhasil")
                    st.write(translation)

    def _display_history(self):
        history = self.history_manager.get_all()
        if history:
            with st.sidebar:
                st.subheader("📜 Riwayat Terjemahan")
                selected_items = []
                
                for idx, item in enumerate(history):
                    col1, col2 = st.columns([0.1, 0.9])
                    with col1:
                        if st.checkbox("", key=f"select_{idx}"):
                            selected_items.append(idx)
                    with col2:
                        with st.expander(f"📄 {item['filename']}"):
                            st.markdown(item["result"])
                
                col1, col2 = st.columns(2)
                with col1:
                    if selected_items:
                        if st.button("🗑️ Hapus Terpilih", key="delete_selected"):
                            self.history_manager.remove_entries(selected_items)
                            st.success("✅ Item terpilih dihapus")
                            st.rerun()
                with col2:
                    if st.button("🗑️ Hapus Semua", key="delete_all"):
                        self.history_manager.clear()
                        st.success("✅ Riwayat dihapus")
                        st.rerun()

if __name__ == "__main__":
    app = TranslatorApp()
    app.run()
