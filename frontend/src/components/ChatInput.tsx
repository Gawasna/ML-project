import React from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({ 
  value, 
  onChange, 
  onSubmit, 
  disabled = false,
  placeholder = "Ask AI to modify pipeline..." 
}: ChatInputProps) {
  return (
    <form 
      onSubmit={onSubmit}
      className="flex items-center justify-between gap-3 p-1.5 bg-white border border-slate-200 rounded-full w-full max-w-lg h-14 shadow-sm hover:border-slate-350 transition-colors duration-150 font-sans"
    >
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="flex-1 bg-transparent px-4 text-sm text-slate-800 placeholder-slate-400 outline-none disabled:cursor-not-allowed"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="flex items-center gap-2 h-10 px-5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-full text-xs font-bold transition-all duration-150 shrink-0 shadow-sm shadow-indigo-100 disabled:shadow-none cursor-pointer"
      >
        <span>Send</span>
        <Send size={12} />
      </button>
    </form>
  );
}
