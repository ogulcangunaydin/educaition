import requests
import os
import logging
from typing import Optional

def get_job_recommendation(personality_scores: dict, gender: str, age: int, education: str, workload: Optional[int] = None, career_start: Optional[int] = None, flexibility: Optional[int] = None) -> str:
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
        f"Aşağıdaki bilgilere dayanarak maddelenmiş bir şekilde uygun 5 meslek önerisi yap."
        f"Her meslek önerisi için, ilgili kişilik özelliğinin sayısal değerine atıfta bulunarak sebep belirt."
        f"Ayrıca, meslek önerisinin kişinin yaşına, mesleğine, cinsiyetine ve çalışma koşullarına nasıl uygun olduğunu da açıkla."
        f"Yanıtları Markdown formatında ver:\n"
        f"Cinsiyet: {gender}\n"
        f"Yaş: {age}\n"
        f"Eğitim Durumu: {education}\n"
        f"Dışadönüklük: {personality_scores['extroversion']}\n"
        f"Uyumluluk: {personality_scores['agreeableness']}\n"
        f"Sorumluluk: {personality_scores['conscientiousness']}\n"
        f"Olumsuz Duygusallık: {personality_scores['negative_emotionality']}\n"
        f"Açık Fikirlilik: {personality_scores['open_mindedness']}\n"
        f"Çalışma Yoğunluğu (1-10): {workload}\n"
        f"Kariyer Başlangıcı (1-10): {career_start}\n"
        f"İş Esnekliği (1-10): {flexibility}\n"
        f"Önerilen Meslekler:\n"
        f"1. **Meslek:** [Meslek Adı]\n"
        f"   **Sebep:** [Bu mesleğin neden uygun olduğunu ve hangi kişilik özelliklerine dayandığını açıklayın.]\n"
        f"2. **Meslek:** [Meslek Adı]\n"
        f"   **Sebep:** [Bu mesleğin neden uygun olduğunu ve hangi kişilik özelliklerine dayandığını açıklayın.]\n"
        f"3. **Meslek:** [Meslek Adı]\n"
        f"   **Sebep:** [Bu mesleğin neden uygun olduğunu ve hangi kişilik özelliklerine dayandığını açıklayın.]\n"
        f"4. **Meslek:** [Meslek Adı]\n"
        f"   **Sebep:** [Bu mesleğin neden uygun olduğunu ve hangi kişilik özelliklerine dayandığını açıklayın.]\n"
        f"5. **Meslek:** [Meslek Adı]\n"
        f"   **Sebep:** [Bu mesleğin neden uygun olduğunu ve hangi kişilik özelliklerine dayandığını açıklayın.]\n"
    )

    job_recommendation = send_request_to_gpt(prompt)
    return job_recommendation