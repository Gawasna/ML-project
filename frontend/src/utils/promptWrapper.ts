/**
 * Prompt wrapper utility.
 *
 * A "wrapper" is a text instruction prepended to the raw user/node prompt
 * before it is sent to the inference backend. Both LiveTab (pipeline) and
 * ChatTab share the same wrapper so behaviour is consistent across modes.
 *
 * Design: keep wrapper definitions data-driven so new ones can be added
 * without touching call-sites — callers only depend on `applyWrapper`.
 */

export interface PromptWrapper {
  id: string;
  label: string;       // shown in the UI toggle chip
  prefix: string;      // text prepended to the raw prompt
  description: string; // tooltip / aria-label
}

export const AVAILABLE_WRAPPERS: PromptWrapper[] = [
  {
    id: 'vi',
    label: 'Dịch VI',
    prefix: 'Dịch sang Tiếng Việt:\n\n',
    description: 'Prepend "Dịch sang Tiếng Việt" so the model translates the output to Vietnamese',
  },
  {
    id: 'summarize',
    label: 'Tóm tắt',
    prefix: 'Tóm tắt ngắn gọn nội dung sau:\n\n',
    description: 'Prepend a Vietnamese summarisation instruction',
  },
  {
    id: 'explain',
    label: 'Giải thích',
    prefix: 'Giải thích đơn giản bằng Tiếng Việt:\n\n',
    description: 'Ask the model to explain the content simply in Vietnamese',
  },
];

/**
 * Applies the active wrapper prefix to a raw prompt.
 * Returns the prompt unchanged when wrapperId is null.
 */
export function applyWrapper(prompt: string, wrapperId: string | null): string {
  if (!wrapperId) return prompt;
  const wrapper = AVAILABLE_WRAPPERS.find(w => w.id === wrapperId);
  if (!wrapper) return prompt;
  return wrapper.prefix + prompt;
}
