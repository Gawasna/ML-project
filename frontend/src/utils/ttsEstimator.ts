/**
 * Estimates Time-To-Speech (TTS) duration for a given text in milliseconds.
 * Supports smart language detection (Vietnamese / English) and pauses for punctuation.
 * 
 * @param text The input text to estimate
 * @returns Estimated duration in milliseconds
 */
export function estimateTTSDuration(text: string): number {
  if (!text || text.trim().length === 0) return 0;

  const trimmedText = text.trim();
  
  // Count words and characters
  const words = trimmedText.split(/\s+/).filter(w => w.length > 0);
  const wordCount = words.length;
  const charCount = trimmedText.length;

  if (wordCount === 0) return 0;

  // Smart Language Detection: Check for Vietnamese accented characters
  const viRegex = /[áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]/i;
  const isVietnamese = viRegex.test(trimmedText);

  // Core reading speed configurations (Words Per Minute)
  const WPM = isVietnamese ? 135 : 145; 
  const MS_PER_WORD = (60 * 1000) / WPM;

  // Base duration from word count
  let duration = wordCount * MS_PER_WORD;

  // Smart feature: punctuation pauses (dấu câu nghỉ ngơi)
  // Commas and colons add minor pause
  const minorPunctuations = (trimmedText.match(/[,:;]/g) || []).length;
  duration += minorPunctuations * (isVietnamese ? 250 : 200);

  // Periods, exclamation marks, question marks add major sentence-boundary pause
  const majorPunctuations = (trimmedText.match(/[.!?]/g) || []).length;
  duration += majorPunctuations * (isVietnamese ? 500 : 450);

  // Character length micro-adjustment (accounts for long words within word boundaries)
  const avgCharPerWord = isVietnamese ? 4.2 : 5.2;
  const actualAvgCharPerWord = charCount / wordCount;
  if (actualAvgCharPerWord > avgCharPerWord * 1.2) {
    // Add 10% duration if words are exceptionally long on average
    duration *= 1.1;
  }

  // Add buffer at start and end of audio (speech engine padding)
  const paddingBuffer = 350;
  duration += paddingBuffer;

  // Enforce realistic bounds:
  // Minimal speech duration is 800ms
  // Max duration is capped at 60 seconds (60000ms) for safety
  return Math.min(Math.max(Math.round(duration), 800), 60000);
}
