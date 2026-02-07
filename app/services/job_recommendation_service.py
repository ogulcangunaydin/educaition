import logging
import os

import requests


def get_job_recommendation(personality_scores: dict) -> str:
    def send_request_to_gpt(prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        }
        data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 1000,
        }
        response = requests.post(
            os.getenv("OPENAI_ENDPOINT"), headers=headers, json=data
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logging.error(
                f"Failed to get response from GPT. Status code: {response.status_code}, Response: {response.text}"
            )
            return None

    prompt = (
        f"Aşağıdaki Big Five kişilik testi puanlarına dayanarak maddelenmiş bir şekilde uygun 5 meslek önerisi yap. "
        f"Her meslek önerisi için, ilgili kişilik özelliğinin sayısal değerine atıfta bulunarak sebep belirt. "
        f"Yanıtları Markdown formatında ver:\n"
        f"Dışadönüklük: {personality_scores['extroversion']:.1f}\n"
        f"Uyumluluk: {personality_scores['agreeableness']:.1f}\n"
        f"Sorumluluk: {personality_scores['conscientiousness']:.1f}\n"
        f"Olumsuz Duygusallık: {personality_scores['negative_emotionality']:.1f}\n"
        f"Açık Fikirlilik: {personality_scores['open_mindedness']:.1f}\n\n"
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
