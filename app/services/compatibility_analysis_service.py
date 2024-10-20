import requests
import os
import logging

def get_compatibility_analysis(personality_scores: dict, star_sign: str, rising_sign: str) -> str:
    def send_request_to_gpt(prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }
        data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 1000
        }
        response = requests.post(os.getenv('OPENAI_ENDPOINT'), headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            logging.error(f"Failed to get response from GPT. Status code: {response.status_code}, Response: {response.text}")
            return None

    prompt = (
        f"Aşağıdaki bilgilere dayanarak yıldız ve yükselen burçların kişilik özellikleriyle uyumluluğunu analiz et."
        f"Her bir kişilik özelliği için, yıldız ve yükselen burçların nasıl etki ettiğini açıkla."
        f"Lütfen samimi ve sen dili kullanarak yaz."
        f"Yanıtları Markdown formatında ver:\n"
        f"Yıldız Burcu: {star_sign}\n"
        f"Yükselen Burcu: {rising_sign}\n"
        f"Dışadönüklük: {personality_scores['extroversion']}\n"
        f"Uyumluluk: {personality_scores['agreeableness']}\n"
        f"Sorumluluk: {personality_scores['conscientiousness']}\n"
        f"Olumsuz Duygusallık: {personality_scores['negative_emotionality']}\n"
        f"Açık Fikirlilik: {personality_scores['open_mindedness']}\n"
        f"Uyumluluk Analizi:\n"
        f"1. **Kişilik Özelliği:** Dışadönüklük\n"
        f"   **Uyumluluk:** [Yıldız ve yükselen burçların dışadönüklük üzerindeki etkisi.]\n"
        f"2. **Kişilik Özelliği:** Uyumluluk\n"
        f"   **Uyumluluk:** [Yıldız ve yükselen burçların uyumluluk üzerindeki etkisi.]\n"
        f"3. **Kişilik Özelliği:** Sorumluluk\n"
        f"   **Uyumluluk:** [Yıldız ve yükselen burçların sorumluluk üzerindeki etkisi.]\n"
        f"4. **Kişilik Özelliği:** Olumsuz Duygusallık\n"
        f"   **Uyumluluk:** [Yıldız ve yükselen burçların olumsuz duygusallık üzerindeki etkisi.]\n"
        f"5. **Kişilik Özelliği:** Açık Fikirlilik\n"
        f"   **Uyumluluk:** [Yıldız ve yükselen burçların açık fikirlilik üzerindeki etkisi.]\n"
    )

    compatibility_analysis = send_request_to_gpt(prompt)
    return compatibility_analysis