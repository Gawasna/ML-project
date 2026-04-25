import React, { useState } from 'react';
import { Settings2, Play, GitBranch, SlidersHorizontal, Square } from 'lucide-react';
import { ModelConfig } from '../types';

interface Props {
  mode: 'split' | 'eval_only';
  setMode: (mode: 'split' | 'eval_only') => void;
  topicName: string;
  setTopicName: (name: string) => void;
  styleName: string;
  setStyleName: (name: string) => void;
  contextDescription: string;
  setContextDescription: (val: string) => void;
  onGenerate: (sourceText: string) => void;
  onStop: () => void;
  isProcessing: boolean;
  progress: number;
  enableEval: boolean;
  setEnableEval: (val: boolean) => void;
  evalRatio: number;
  setEvalRatio: (val: number) => void;
  modelConfig: ModelConfig;
  setModelConfig: (config: ModelConfig) => void;
  isReverseMode: boolean;
  setIsReverseMode: (val: boolean) => void;
}

export function ConfigurationZone({
  mode,
  setMode,
  topicName,
  setTopicName,
  styleName,
  setStyleName,
  contextDescription,
  setContextDescription,
  onGenerate,
  onStop,
  isProcessing,
  progress,
  enableEval,
  setEnableEval,
  evalRatio,
  setEvalRatio,
  modelConfig,
  setModelConfig,
  isReverseMode,
  setIsReverseMode
}: Props) {
  const [sourceText, setSourceText] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  return (
    <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col gap-5">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
        <div className="flex items-center gap-2">
          <Settings2 className="w-5 h-5 text-zinc-400" />
          <h2 className="text-lg font-medium text-zinc-100">Cấu hình tham số</h2>
        </div>
        
        <div className="flex bg-zinc-950 rounded-lg p-1 border border-zinc-800">
          <button
            onClick={() => setMode('split')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              mode === 'split' 
                ? 'bg-zinc-800 text-zinc-100' 
                : 'text-zinc-400 hover:text-zinc-300'
            }`}
          >
            Train & Eval
          </button>
          <button
            onClick={() => setMode('eval_only')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              mode === 'eval_only' 
                ? 'bg-zinc-800 text-zinc-100' 
                : 'text-zinc-400 hover:text-zinc-300'
            }`}
          >
            Eval Only
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Chủ đề (Topic) <span className="text-red-400">*</span></label>
          <input 
            type="text"
            value={topicName}
            onChange={e => setTopicName(e.target.value)}
            placeholder="VD: Y khoa, Luật sư, Lập trình..."
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-zinc-100 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-all"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Phong cách (Style) <span className="text-zinc-500 lowercase normal-case">(Tùy chọn)</span></label>
          <input 
            type="text"
            value={styleName}
            onChange={e => setStyleName(e.target.value)}
            placeholder="VD: Hài hước, Cổ tích, Cướp biển..."
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-zinc-100 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-all"
          />
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Mô tả bối cảnh <span className="text-zinc-500 lowercase normal-case">(Tùy chọn)</span></label>
        <input 
          type="text"
          value={contextDescription}
          onChange={e => setContextDescription(e.target.value)}
          placeholder="Mô tả bối cảnh..."
          className="bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-zinc-100 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-all"
        />
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Dữ liệu nguồn (Văn bản thô)</label>
          <div className="flex items-center gap-2">
            <label className="text-xs text-zinc-400 cursor-pointer" onClick={() => setIsReverseMode(!isReverseMode)}>
              Chế độ tương thích ngược (Input Tiếng Việt)
            </label>
            <button
              onClick={() => setIsReverseMode(!isReverseMode)}
              className={`relative inline-flex h-4 w-7 items-center rounded-full transition-colors ${
                isReverseMode ? 'bg-indigo-500' : 'bg-zinc-700'
              }`}
            >
              <span
                className={`inline-block h-2.5 w-2.5 transform rounded-full bg-white transition-transform ${
                  isReverseMode ? 'translate-x-3.5' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
        <textarea 
          value={sourceText}
          onChange={e => setSourceText(e.target.value)}
          placeholder={isReverseMode ? "Dán văn bản tiếng Việt thô vào đây..." : "Dán văn bản thô vào đây. Hệ thống sẽ tự động phân tách thành các đoạn nhỏ..."}
          className="bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-sm text-zinc-100 h-40 resize-y focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-all font-mono"
        />
      </div>

      <div className="flex flex-col gap-3 bg-zinc-950/50 p-4 rounded-lg border border-zinc-800/50">
        <button 
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center justify-between w-full group"
        >
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-zinc-400 group-hover:text-zinc-300 transition-colors" />
            <label className="text-sm font-medium text-zinc-300 group-hover:text-zinc-200 transition-colors cursor-pointer">Cấu hình Mô hình (Nâng cao)</label>
          </div>
          <span className="text-xs text-zinc-500">{showAdvanced ? 'Thu gọn' : 'Mở rộng'}</span>
        </button>
        
        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2 pt-3 border-t border-zinc-800/50">
            <div className="flex flex-col gap-2">
              <div className="flex justify-between">
                <label className="text-xs text-zinc-400">Temperature</label>
                <span className="text-xs text-zinc-500 font-mono">{modelConfig.temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={modelConfig.temperature}
                onChange={(e) => setModelConfig({...modelConfig, temperature: parseFloat(e.target.value)})}
                className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-zinc-400"
              />
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex justify-between">
                <label className="text-xs text-zinc-400">Top P</label>
                <span className="text-xs text-zinc-500 font-mono">{modelConfig.topP}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={modelConfig.topP}
                onChange={(e) => setModelConfig({...modelConfig, topP: parseFloat(e.target.value)})}
                className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-zinc-400"
              />
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex justify-between">
                <label className="text-xs text-zinc-400">Top K</label>
                <span className="text-xs text-zinc-500 font-mono">{modelConfig.topK}</span>
              </div>
              <input
                type="range"
                min="1"
                max="100"
                step="1"
                value={modelConfig.topK}
                onChange={(e) => setModelConfig({...modelConfig, topK: parseInt(e.target.value)})}
                className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-zinc-400"
              />
            </div>
          </div>
        )}
      </div>

      {mode === 'split' && (
        <div className="flex flex-col gap-3 bg-zinc-950/50 p-4 rounded-lg border border-zinc-800/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-indigo-400" />
              <label className="text-sm font-medium text-zinc-300">Tách dữ liệu Đánh giá (Eval/Validation)</label>
            </div>
            <button
              onClick={() => setEnableEval(!enableEval)}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                enableEval ? 'bg-indigo-500' : 'bg-zinc-700'
              }`}
            >
              <span
                className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                  enableEval ? 'translate-x-4' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          
          {enableEval && (
            <div className="flex items-center gap-4 mt-1">
              <span className="text-xs text-zinc-500 w-12">{evalRatio}%</span>
              <input
                type="range"
                min="5"
                max="30"
                step="5"
                value={evalRatio}
                onChange={(e) => setEvalRatio(parseInt(e.target.value))}
                className="flex-1 h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
              <span className="text-xs text-zinc-500">Tỷ lệ Eval</span>
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-between pt-2">
        <div className="flex-1">
          {isProcessing && (
            <div className="flex items-center gap-3">
              <div className="w-48 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-zinc-400 transition-all duration-300 ease-out"
                  style={{ width: `${Math.round(progress * 100)}%` }}
                />
              </div>
              <span className="text-xs text-zinc-500 font-mono">{Math.round(progress * 100)}%</span>
            </div>
          )}
        </div>
        {isProcessing ? (
          <button
            onClick={onStop}
            className="flex items-center gap-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 px-6 py-2.5 rounded-lg text-sm font-medium transition-colors border border-red-500/20"
          >
            <Square className="w-4 h-4 fill-current" />
            Dừng xử lý
          </button>
        ) : (
          <button
            onClick={() => onGenerate(sourceText)}
            disabled={isProcessing}
            className="flex items-center gap-2 bg-zinc-100 text-zinc-900 hover:bg-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="w-4 h-4" />
            Tạo tập dữ liệu
          </button>
        )}
      </div>
    </section>
  );
}
