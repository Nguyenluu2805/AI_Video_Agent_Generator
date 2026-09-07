import asyncio
import edge_tts

async def main():
    voices = await edge_tts.list_voices()
    print(f"Total voices: {len(voices)}")
    print("--- Vietnamese voices ---")
    for v in voices:
        if "VN" in v["Locale"]:
            print(v["ShortName"], v["Gender"], v["Locale"])
            
    print("--- Multilingual voices ---")
    for v in voices:
        if "multilingual" in v["ShortName"].lower():
            print(v["ShortName"], v["Gender"], v["Locale"])

asyncio.run(main())
