import React, { useState, useRef } from 'react';
import { ConfigurationZone } from './components/ConfigurationZone';
import { DataReviewZone } from './components/DataReviewZone';
import { ExportZone } from './components/ExportZone';
import { DatasetItem, ModelConfig } from './types';
import { splitTextIntoChunks } from './utils/textSplitter';
import { processAllChunks } from './services/gemini';

export default function App() {
  const [items, setItems] = useState<DatasetItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const [topicName, setTopicName] = useState("");
  const [styleName, setStyleName] = useState("");
  const [contextDescription, setContextDescription] = useState("");
  const [mode, setMode] = useState<'split' | 'eval_only'>('split');
  const [enableEval, setEnableEval] = useState(false);
  const [evalRatio, setEvalRatio] = useState(10);
  const [isReverseMode, setIsReverseMode] = useState(false);
  const [modelConfig, setModelConfig] = useState<ModelConfig>({
    temperature: 0.7,
    topP: 0.95,
    topK: 40,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const handleGenerate = async (sourceText: string) => {
    if (!topicName.trim()) {
      setError("Vui lòng nhập Chủ đề (bắt buộc).");
      return;
    }
    if (!sourceText.trim()) {
      setError("Vui lòng nhập Dữ liệu nguồn.");
      return;
    }

    setError(null);
    setIsProcessing(true);
    setProgress(0);
    setItems([]);

    abortControllerRef.current = new AbortController();

    try {
      const chunks = splitTextIntoChunks(sourceText);
      if (chunks.length === 0) {
        throw new Error("Không tìm thấy dữ liệu hợp lệ để xử lý.");
      }

      await processAllChunks(
        chunks, 
        topicName, 
        styleName, 
        contextDescription, 
        modelConfig, 
        isReverseMode,
        (prog, newItems) => {
          setProgress(prog);
          const processedItems = newItems.map(item => {
            const isEvalItem = mode === 'eval_only' ? true : (enableEval && Math.random() < (evalRatio / 100));
            return {
              ...item,
              isEval: isEvalItem,
              id: isEvalItem ? `eval-${item.id}` : `train-${item.id}`
            };
          });
          setItems(prev => [...prev, ...processedItems]);
        },
        abortControllerRef.current.signal
      );
    } catch (err: any) {
      if (err.name === 'AbortError' || err.message === 'Đã dừng xử lý.') {
        setError("Đã dừng quá trình xử lý.");
      } else {
        setError(err.message || "Đã xảy ra lỗi trong quá trình xử lý.");
      }
    } finally {
      setIsProcessing(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const handleUpdateItem = (id: string, field: keyof DatasetItem, value: string) => {
    setItems(prev => prev.map(item => item.id === id ? { ...item, [field]: value } : item));
  };

  const handleDeleteItem = (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-300 font-sans p-6 flex flex-col gap-6">
      <header className="border-b border-zinc-800 pb-4">
        <h1 className="text-2xl font-semibold text-zinc-100 tracking-tight">LoRA Dataset Architect</h1>
        <p className="text-sm text-zinc-500 mt-1">Hệ thống chuẩn bị dữ liệu Instruction Tuning</p>
      </header>

      <main className="flex-1 flex flex-col gap-6 max-w-7xl mx-auto w-full">
        {error && (
          <div className="bg-red-950/50 border border-red-900/50 text-red-400 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        )}

        <ConfigurationZone 
          mode={mode}
          setMode={setMode}
          topicName={topicName}
          setTopicName={setTopicName}
          styleName={styleName}
          setStyleName={setStyleName}
          contextDescription={contextDescription}
          setContextDescription={setContextDescription}
          onGenerate={handleGenerate}
          onStop={handleStop}
          isProcessing={isProcessing}
          progress={progress}
          enableEval={enableEval}
          setEnableEval={setEnableEval}
          evalRatio={evalRatio}
          setEvalRatio={setEvalRatio}
          modelConfig={modelConfig}
          setModelConfig={setModelConfig}
          isReverseMode={isReverseMode}
          setIsReverseMode={setIsReverseMode}
        />

        <DataReviewZone 
          items={items}
          onUpdateItem={handleUpdateItem}
          onDeleteItem={handleDeleteItem}
        />

        <ExportZone 
          items={items}
          topicName={topicName}
          styleName={styleName}
          mode={mode}
        />
      </main>
    </div>
  );
}
