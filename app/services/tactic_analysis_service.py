"""
Tactic Analysis Service

GPT-powered analysis of Prisoner's Dilemma tactics:
1. Generate probable reasons why a student chose their tactic
2. Generate job recommendations based on tactic + selected reason

Language-aware: supports Turkish and English prompts.
"""

import json
import logging
import os

import requests


def _send_request_to_gpt(prompt: str, max_tokens: int = 1000, temperature: float = 0.6) -> str | None:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
    }
    data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        response = requests.post(
            os.getenv("OPENAI_ENDPOINT"), headers=headers, json=data
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logging.error(
                f"Failed to get response from GPT. "
                f"Status code: {response.status_code}, Response: {response.text}"
            )
            return None
    except Exception as e:
        logging.error(f"Error calling GPT API: {e}")
        return None


def generate_tactic_reasons(tactic: str, language: str = "tr") -> list[str]:
    """
    Generate 5 probable psychological/strategic reasons why a student
    would choose a given Prisoner's Dilemma tactic.

    Returns a list of reason strings.
    """
    if language == "tr":
        prompt = (
            f"Bir öğrenci Mahkum İkilemi (Prisoner's Dilemma) oyun teorisi deneyi için şu stratejiyi yazdı:\n\n"
            f'"{tactic}"\n\n'
            f"Bu stratejiyi seçmenin arkasında yatabilecek 5 farklı psikolojik veya stratejik nedeni yaz. "
            f"Her neden, öğrencinin kişiliği, değerleri, dünya görüşü veya karar verme tarzı hakkında "
            f"farklı bir şey ortaya koymalıdır. Nedenler kısa ve anlaşılır olmalı (her biri 1-2 cümle).\n\n"
            f"Yanıtı YALNIZCA şu formatta bir JSON dizisi olarak ver, başka hiçbir şey yazma:\n"
            f'["Neden 1", "Neden 2", "Neden 3", "Neden 4", "Neden 5"]'
        )
    else:
        prompt = (
            f"A student wrote the following strategy for the Prisoner's Dilemma game theory experiment:\n\n"
            f'"{tactic}"\n\n'
            f"Write 5 distinct psychological or strategic reasons why someone would choose this strategy. "
            f"Each reason should reveal something different about the student's personality, values, "
            f"worldview, or decision-making style. Keep each reason concise (1-2 sentences).\n\n"
            f"Return ONLY a JSON array in this format, nothing else:\n"
            f'["Reason 1", "Reason 2", "Reason 3", "Reason 4", "Reason 5"]'
        )

    response = _send_request_to_gpt(prompt, max_tokens=800, temperature=0.7)

    if not response:
        return _get_fallback_reasons(language)

    try:
        # Clean up the response - GPT sometimes wraps in ```json blocks
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            cleaned = cleaned.rsplit("```", 1)[0].strip()
        
        reasons = json.loads(cleaned)
        if isinstance(reasons, list) and len(reasons) >= 3:
            return reasons[:5]
    except (json.JSONDecodeError, TypeError) as e:
        logging.error(f"Failed to parse tactic reasons JSON: {e}, response: {response}")

    return _get_fallback_reasons(language)


def _get_fallback_reasons(language: str) -> list[str]:
    """Fallback reasons if GPT fails."""
    if language == "tr":
        return [
            "Güven ve işbirliğine dayalı ilişkilerin uzun vadede daha verimli olduğunu düşünüyorum.",
            "Rekabetçi ortamlarda en iyi bireysel sonucu elde etmenin önemli olduğuna inanıyorum.",
            "Adalet ve karşılıklılık ilkelerine göre hareket etmeyi tercih ediyorum.",
            "Stratejik düşünme ve rakibin davranışlarını analiz etme benim güçlü yanım.",
            "Esnek olmayı ve duruma göre kararlarımı değiştirmeyi tercih ediyorum.",
        ]
    else:
        return [
            "I believe trust and cooperative relationships are more productive in the long run.",
            "I think achieving the best individual outcome in competitive environments is important.",
            "I prefer to act based on principles of fairness and reciprocity.",
            "Strategic thinking and analyzing opponent behavior is my strength.",
            "I prefer being flexible and adapting my decisions based on the situation.",
        ]


def generate_job_recommendation(tactic: str, reason: str, language: str = "tr") -> str:
    """
    Generate job recommendations based on a student's Prisoner's Dilemma tactic
    and their selected reason for choosing it.

    Returns a Markdown-formatted string with analysis and 5 job suggestions.
    """
    if language == "tr":
        prompt = (
            f"Bir öğrenci Mahkum İkilemi (Prisoner's Dilemma) oyun teorisi deneyinde şu stratejiyi yazdı:\n\n"
            f"**Strateji:** {tactic}\n\n"
            f"**Bu stratejiyi seçme nedeni:** {reason}\n\n"
            f"Mahkum İkilemi'nde bir oyuncunun stratejisi, onun kişilik özelliklerini ortaya koyar:\n"
            f"- İşbirliği eğilimi → Güven, takım çalışması, empati, sosyal sorumluluk\n"
            f"- İhanet/rekabet eğilimi → Rekabetçilik, bireyselcilik, risk alma, sonuç odaklılık\n"
            f"- Kısasa kısas/karşılıklılık → Adalet duygusu, tutarlılık, prensipli yaklaşım\n"
            f"- Affedici stratejiler → Duygusal zeka, esneklik, uzlaşmacılık\n"
            f"- Karmaşık/analitik stratejiler → Analitik düşünce, planlama, veri odaklı karar verme\n"
            f"- Savunmacı stratejiler → Temkinlilik, risk yönetimi, güvenlik odaklılık\n\n"
            f"Bu bilgilere dayanarak aşağıdaki analizi Markdown formatında yap:\n\n"
            f"## 🎯 Kişilik Analizi\n"
            f"Öğrencinin strateji ve neden seçiminden ortaya çıkan kişilik özelliklerini kısaca analiz et "
            f"(3-4 cümle). Stratejinin oyundaki yaklaşımı ve seçilen nedenin ne tür bir düşünce yapısını "
            f"yansıttığını açıkla.\n\n"
            f"## 💼 Kariyer Önerileri\n"
            f"Bu özelliklere uygun 5 meslek önerisi sun. Her öneri için:\n"
            f"- **Meslek Adı**\n"
            f"- **Neden Uygun**: Stratejideki ve seçilen nedendeki hangi kişilik özelliklerinin "
            f"bu mesleğe uyduğunu 1-2 cümleyle açıkla.\n\n"
            f"## 🌟 Genel Değerlendirme\n"
            f"2-3 cümlelik cesaretlendirici ve motive edici bir genel değerlendirme yaz. "
            f"Stratejinin güçlü yönlerini vurgula.\n\n"
            f"Yanıtı tamamen Türkçe ver. Samimi, cesaretlendirici ve öğrenci dostu bir ton kullan. "
            f"Sonuçların ilham verici olduğunu ama kesin olmadığını belirt."
        )
    else:
        prompt = (
            f"A student wrote the following strategy for the Prisoner's Dilemma game theory experiment:\n\n"
            f"**Strategy:** {tactic}\n\n"
            f"**Reason for choosing this strategy:** {reason}\n\n"
            f"In the Prisoner's Dilemma, a player's strategy reveals personality traits:\n"
            f"- Cooperation tendency → Trust, teamwork, empathy, social responsibility\n"
            f"- Defection/competition tendency → Competitiveness, individualism, risk-taking, results-orientation\n"
            f"- Tit-for-tat/reciprocity → Sense of justice, consistency, principled approach\n"
            f"- Forgiving strategies → Emotional intelligence, flexibility, conciliation\n"
            f"- Complex/analytical strategies → Analytical thinking, planning, data-driven decisions\n"
            f"- Defensive strategies → Caution, risk management, security-orientation\n\n"
            f"Based on this information, create the following analysis in Markdown format:\n\n"
            f"## 🎯 Personality Analysis\n"
            f"Briefly analyze the personality traits revealed by the student's strategy and reason "
            f"(3-4 sentences). Explain what the strategy reveals about their approach and what the "
            f"selected reason tells about their thinking style.\n\n"
            f"## 💼 Career Suggestions\n"
            f"Suggest 5 suitable careers. For each:\n"
            f"- **Career Name**\n"
            f"- **Why it fits**: Explain in 1-2 sentences which personality traits from the strategy "
            f"and reason make this career a good fit.\n\n"
            f"## 🌟 Overall Assessment\n"
            f"Write a 2-3 sentence encouraging and motivating overall assessment. "
            f"Highlight the strengths revealed by their strategy.\n\n"
            f"Use a friendly, encouraging, student-oriented tone. "
            f"Note that results are inspirational but not definitive."
        )

    response = _send_request_to_gpt(prompt, max_tokens=1500, temperature=0.6)

    if not response:
        if language == "tr":
            return "Kariyer önerisi şu anda oluşturulamadı. Lütfen daha sonra tekrar deneyin."
        return "Career suggestion could not be generated at this time. Please try again later."

    return response
