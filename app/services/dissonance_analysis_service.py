import logging
import os

import requests


def get_dissonance_analysis(participant_data: dict) -> str:
    """
    Generate a GPT-powered dissonance analysis and job recommendation
    based on the cognitive dissonance test results.

    Analyses how easily the student is affected by social/environmental
    influence by comparing first vs second round taxi answers with
    the displayed (fake) averages.
    """

    def send_request_to_gpt(prompt: str) -> str | None:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        }
        data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "max_tokens": 1500,
        }
        response = requests.post(
            os.getenv("OPENAI_ENDPOINT"), headers=headers, json=data
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logging.error(
                f"Failed to get dissonance analysis from GPT. "
                f"Status code: {response.status_code}, Response: {response.text}"
            )
            return None

    # Extract participant data with safe defaults
    class_year = participant_data.get("education") or "Belirtilmedi"
    gender = participant_data.get("gender") or "Belirtilmedi"
    star_sign = participant_data.get("star_sign") or "Belirtilmedi"
    rising_sign = participant_data.get("rising_sign") or "Belirtilmedi"
    workload = participant_data.get("workload") or "Belirtilmedi"
    career_start = participant_data.get("career_start") or "Belirtilmedi"
    flexibility = participant_data.get("flexibility") or "Belirtilmedi"

    comfort_first = participant_data.get("comfort_question_first_answer", "-")
    comfort_avg = participant_data.get("comfort_question_displayed_average", "-")
    comfort_second = participant_data.get("comfort_question_second_answer", "-")

    fare_first = participant_data.get("fare_question_first_answer", "-")
    fare_avg = participant_data.get("fare_question_displayed_average", "-")
    fare_second = participant_data.get("fare_question_second_answer", "-")

    prompt = (
        f"Bir öğrencinin bilişsel uyumsuzluk testi sonuçlarını analiz et ve kariyer önerisi yap.\n\n"
        f"## Öğrenci Bilgileri\n"
        f"- Sınıf: {class_year}\n"
        f"- Cinsiyet: {gender}\n"
        f"- Burç: {star_sign}\n"
        f"- Yükselen Burç: {rising_sign}\n\n"
        f"## Kariyer Tercihleri\n"
        f"- İş temposu tercihi (1=Rahat, 10=Yoğun): {workload}\n"
        f"- Kariyer başlangıcı tercihi (1=Kolay, 10=Zorlu): {career_start}\n"
        f"- Esneklik tercihi (1=Katı, 10=Esnek): {flexibility}\n\n"
        f"## Bilişsel Uyumsuzluk Testi Sonuçları\n"
        f"(Öğrenci bir taksi hizmeti değerlendirmesi yaptı. İlk cevabını verdikten sonra "
        f"kendisine sahte bir ortalama gösterildi ve tekrar cevaplaması istendi. "
        f"İlk ve ikinci cevap arasındaki fark, öğrencinin çevresel etkiye açıklığını gösterir.)\n\n"
        f"### Taksi Hizmeti Konforu Sorusu (1-10)\n"
        f"- İlk cevap (kendi düşüncesi): {comfort_first}\n"
        f"- Gösterilen ortalama: {comfort_avg}\n"
        f"- İkinci cevap (ortalamayı gördükten sonra): {comfort_second}\n\n"
        f"### Taksi Ücret Dengesi Sorusu (1-10)\n"
        f"- İlk cevap (kendi düşüncesi): {fare_first}\n"
        f"- Gösterilen ortalama: {fare_avg}\n"
        f"- İkinci cevap (ortalamayı gördükten sonra): {fare_second}\n\n"
        f"## Görev\n"
        f"Aşağıdaki analizi Markdown formatında yap:\n\n"
        f"1. **Çevresel Etki Analizi**: İlk ve ikinci cevaplar arasındaki farkı analiz et. "
        f"Öğrenci gösterilen ortalamaya doğru mu yaklaştı, uzaklaştı mı yoksa aynı mı kaldı? "
        f"Bu durum öğrencinin çevresel etkilere ve sosyal baskıya ne kadar açık olduğunu gösterir. "
        f"Kısa ve öğrenci dostu bir dille değerlendir.\n\n"
        f"2. **Kariyer Önerileri**: Öğrencinin sınıf düzeyini, kariyer tercihlerini (iş temposu, "
        f"kariyer başlangıcı, esneklik), burç özelliklerini ve çevresel etkiye açıklık düzeyini "
        f"dikkate alarak 5 kariyer önerisi sun. Her öneri için:\n"
        f"   - **Meslek Adı**\n"
        f"   - **Neden uygun**: Hangi özelliklere dayandığını kısaca açıkla\n\n"
        f"3. **Genel Değerlendirme**: 2-3 cümlelik genel bir değerlendirme ve motivasyon cümlesi yaz.\n\n"
        f"Yanıtı tamamen Türkçe ver. Samimi ve cesaretlendirici bir ton kullan. "
        f"Sonuçların ilham verici olduğunu ama kesin olmadığını belirt."
    )

    return send_request_to_gpt(prompt)
