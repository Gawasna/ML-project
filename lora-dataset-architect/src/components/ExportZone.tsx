import React from 'react';
import { DatasetItem } from '../types';
import { Download } from 'lucide-react';

interface Props {
  items: DatasetItem[];
  topicName: string;
  styleName: string;
  mode: 'split' | 'eval_only';
}

export function ExportZone({ items, topicName, styleName, mode }: Props) {
  const handleDownload = () => {
    if (items.length === 0) return;

    const safeTargetName = topicName.trim().replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'untitled';
    const safeStyleName = styleName.trim().replace(/[^a-z0-9]/gi, '_').toLowerCase();
    const uniqueId = Math.random().toString(36).substring(2, 8);

    const trainItems = items.filter(i => !i.isEval);
    const evalItems = items.filter(i => i.isEval);

    const downloadFile = (data: DatasetItem[], suffix: string) => {
      if (data.length === 0) return;
      
      const jsonlContent = data.map(item => JSON.stringify({
        instruction: item.instruction,
        input: item.input,
        output: item.output
      })).join('\n');

      const blob = new Blob([jsonlContent], { type: 'application/jsonl' });
      const url = URL.createObjectURL(blob);
      
      let filename = '';
      if (mode === 'eval_only') {
        filename = `dataset-${safeTargetName}-eval-${uniqueId}.jsonl`;
      } else {
        filename = `dataset-${safeTargetName}${safeStyleName ? `-${safeStyleName}` : ''}-${suffix}-${uniqueId}.jsonl`;
      }

      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    };

    if (evalItems.length > 0) {
      downloadFile(trainItems, 'train');
      // Thêm một chút delay để trình duyệt không chặn tải xuống nhiều file
      setTimeout(() => {
        downloadFile(evalItems, 'eval');
      }, 500);
    } else {
      downloadFile(items, 'full');
    }
  };

  return (
    <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex items-center justify-between">
      <div className="flex flex-col">
        <h2 className="text-sm font-medium text-zinc-100">Xuất dữ liệu</h2>
        <p className="text-xs text-zinc-500 mt-1">Định dạng JSONL (mỗi dòng là một đối tượng JSON độc lập)</p>
      </div>
      
      <button
        onClick={handleDownload}
        disabled={items.length === 0}
        className="flex items-center gap-2 bg-zinc-800 text-zinc-100 hover:bg-zinc-700 px-5 py-2.5 rounded-lg text-sm font-medium transition-colors border border-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Download className="w-4 h-4" />
        Tải xuống JSONL
      </button>
    </section>
  );
}
