from app.core.config import settings

class CostCalculator:
    async def calculate(self, data: dict) -> dict:
        """
        Input: Raw usage stats (duration, tokens).
        Output: Cost breakdown.
        """
        duration_min = float(data.get("duration_seconds", 0)) / 60.0
        
        # 1. STT Cost (Deepgram)
        stt_cost = duration_min * settings.PRICE_STT_PER_MIN
        
        # 2. Telephony Cost (Twilio)
        twilio_cost = duration_min * settings.PRICE_TWILIO_PER_MIN
        
        # 3. LLM Cost (OpenAI)
        input_tokens = int(data.get("input_tokens", 0))
        output_tokens = int(data.get("output_tokens", 0))
        
        llm_cost = (input_tokens / 1000 * settings.PRICE_LLM_INPUT_1K) + \
                   (output_tokens / 1000 * settings.PRICE_LLM_OUTPUT_1K)
        
        # 4. TTS Cost (ElevenLabs)
        tts_chars = int(data.get("tts_characters", 0))
        tts_cost = (tts_chars / 1000) * settings.PRICE_TTS_1K_CHARS
        
        # Subtotal
        raw_cost = stt_cost + twilio_cost + llm_cost + tts_cost
        
        # Apply Margin
        total_cost = raw_cost * (1 + settings.PROFIT_MARGIN_PERCENT)
        
        return {
            "total_cost": round(total_cost, 4),
            "breakdown": {
                "stt": stt_cost,
                "twilio": twilio_cost,
                "llm": llm_cost,
                "tts": tts_cost,
                "margin": total_cost - raw_cost
            }
        }