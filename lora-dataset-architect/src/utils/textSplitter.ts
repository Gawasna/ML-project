export function splitTextIntoChunks(text: string): string[] {
  const chunks: string[] = [];
  
  // 1. Normalize text: remove extra whitespace, replace newlines with spaces
  // This helps join broken subtitle lines
  let normalizedText = text.replace(/\r\n/g, ' ').replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
  
  // 2. Split into sentences
  // Matches anything ending in . ? or ! followed by a space or end of string
  // Also handles cases where there might be quotes after punctuation
  const sentenceRegex = /[^.?!]+[.?!]+["']?(?=\s|$)|[^.?!]+$/g;
  const sentences = normalizedText.match(sentenceRegex);
  
  if (!sentences) {
    // Fallback if no punctuation found at all
    // Split by length roughly every 150 chars, trying to break at spaces
    let current = normalizedText;
    while (current.length > 0) {
      if (current.length <= 150) {
        chunks.push(current.trim());
        break;
      }
      let breakPoint = current.lastIndexOf(' ', 150);
      if (breakPoint === -1) breakPoint = 150;
      chunks.push(current.substring(0, breakPoint).trim());
      current = current.substring(breakPoint).trim();
    }
    return chunks;
  }

  // 3. Group sentences into small chunks (1-2 sentences, max ~200 chars)
  const MAX_CHUNK_LENGTH = 200;
  let currentChunk = "";

  for (let i = 0; i < sentences.length; i++) {
    const sentence = sentences[i].trim();
    if (!sentence) continue;

    // If the sentence itself is very long, just add it as its own chunk
    if (sentence.length > MAX_CHUNK_LENGTH) {
      if (currentChunk) {
        chunks.push(currentChunk.trim());
        currentChunk = "";
      }
      chunks.push(sentence);
      continue;
    }

    // If adding this sentence exceeds our preferred length, push the current chunk
    if (currentChunk && (currentChunk + " " + sentence).length > MAX_CHUNK_LENGTH) {
      chunks.push(currentChunk.trim());
      currentChunk = sentence;
    } else {
      // Otherwise, append it
      currentChunk += (currentChunk ? " " : "") + sentence;
    }
  }

  if (currentChunk) {
    chunks.push(currentChunk.trim());
  }

  return chunks;
}
